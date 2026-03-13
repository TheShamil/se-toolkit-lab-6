#!/usr/bin/env python3
"""
Agent CLI - Calls an LLM with tools to answer questions using project documentation.

Usage:
    uv run agent.py "Your question here"

Output:
    JSON with "answer", "source", and "tool_calls" fields to stdout.
    All debug output goes to stderr.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Maximum tool calls per question
MAX_TOOL_CALLS = 10


def load_config() -> dict:
    """Load configuration from .env.agent.secret file."""
    env_path = Path(__file__).parent / ".env.agent.secret"
    load_dotenv(env_path)

    config = {
        "api_key": os.getenv("LLM_API_KEY"),
        "api_base": os.getenv("LLM_API_BASE"),
        "model": os.getenv("LLM_MODEL"),
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"Error: Missing configuration: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    return config


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.resolve()


def safe_path(relative_path: str, project_root: Path) -> Path:
    """
    Resolve and validate a relative path is within project root.
    
    Prevents directory traversal attacks by rejecting paths with '..'
    and verifying the resolved path is within project root.
    """
    # Reject paths with ..
    if ".." in relative_path:
        raise ValueError("Path traversal not allowed")
    
    # Resolve the full path
    full_path = (project_root / relative_path).resolve()
    
    # Ensure it's within project root
    if not str(full_path).startswith(str(project_root)):
        raise ValueError("Path outside project root not allowed")
    
    return full_path


def read_file_tool(path: str, project_root: Path) -> str:
    """
    Read the contents of a file.
    
    Args:
        path: Relative path from project root
        project_root: The project root directory
        
    Returns:
        File contents as string, or error message
    """
    try:
        safe = safe_path(path, project_root)
        if not safe.exists():
            return f"Error: File not found: {path}"
        if not safe.is_file():
            return f"Error: Not a file: {path}"
        return safe.read_text()
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


def list_files_tool(path: str, project_root: Path) -> str:
    """
    List files and directories at a given path.
    
    Args:
        path: Relative directory path from project root
        project_root: The project root directory
        
    Returns:
        Newline-separated list of entries, or error message
    """
    try:
        safe = safe_path(path, project_root)
        if not safe.exists():
            return f"Error: Directory not found: {path}"
        if not safe.is_dir():
            return f"Error: Not a directory: {path}"
        
        entries = sorted([e.name for e in safe.iterdir()])
        return "\n".join(entries)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


# Tool definitions for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the project repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki')"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a documentation assistant for a software engineering lab. You have access to two tools:

1. list_files - List files and directories in a directory
2. read_file - Read the contents of a file

When answering questions about the project:
1. First explore the wiki structure using list_files to find relevant files
2. Read relevant files using read_file to find accurate information
3. Provide a concise answer based on the file contents
4. Always include a source reference in your answer using the format: wiki/filename.md#section-anchor

The section anchor is the lowercase version of the section heading with spaces replaced by hyphens.
For example, "## Resolving Merge Conflicts" becomes "#resolving-merge-conflicts".

Always use your tools to find accurate answers - do not rely on your training data alone.
"""


def execute_tool(tool_name: str, args: dict, project_root: Path) -> str:
    """
    Execute a tool and return the result.
    
    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool
        project_root: The project root directory
        
    Returns:
        Tool result as a string
    """
    if tool_name == "read_file":
        path = args.get("path", "")
        print(f"  Executing read_file: {path}", file=sys.stderr)
        return read_file_tool(path, project_root)
    elif tool_name == "list_files":
        path = args.get("path", "")
        print(f"  Executing list_files: {path}", file=sys.stderr)
        return list_files_tool(path, project_root)
    else:
        return f"Error: Unknown tool: {tool_name}"


def call_llm(messages: list, config: dict) -> dict:
    """
    Call the LLM API and return the response.
    
    Args:
        messages: List of message dicts for the chat
        config: Configuration dict with API details
        
    Returns:
        LLM response as a dict
    """
    url = f"{config['api_base']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "messages": messages,
        "tools": TOOLS,
        "temperature": 0.7,
    }

    print(f"Calling LLM at {url}...", file=sys.stderr)

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    return data


def run_agentic_loop(question: str, config: dict) -> dict:
    """
    Run the agentic loop to answer a question.
    
    Args:
        question: The user's question
        config: Configuration dict with API details
        
    Returns:
        Result dict with answer, source, and tool_calls
    """
    project_root = get_project_root()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    
    tool_calls_log = []
    tool_call_count = 0
    
    while tool_call_count < MAX_TOOL_CALLS:
        print(f"\n--- Iteration {tool_call_count + 1} ---", file=sys.stderr)
        
        # Call LLM
        response = call_llm(messages, config)
        message = response["choices"][0]["message"]
        
        # Check for tool calls
        tool_calls = message.get("tool_calls", [])
        
        if not tool_calls:
            # No tool calls - LLM provided final answer
            print("LLM provided final answer (no tool calls)", file=sys.stderr)
            answer = message.get("content", "")
            
            # Try to extract source from the answer
            source = extract_source(answer)
            
            return {
                "answer": answer,
                "source": source,
                "tool_calls": tool_calls_log,
            }
        
        # Process tool calls
        print(f"LLM requested {len(tool_calls)} tool call(s)", file=sys.stderr)
        
        # Add assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
        })
        
        # Execute each tool call
        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            
            result = execute_tool(tool_name, tool_args, project_root)
            
            # Log the tool call
            tool_calls_log.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result,
            })
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result,
            })
            
            tool_call_count += 1
    
    # Max tool calls reached
    print(f"Maximum tool calls ({MAX_TOOL_CALLS}) reached", file=sys.stderr)
    
    # Try to get an answer from the last message or provide a fallback
    answer = "I've reached the maximum number of tool calls. Based on the information gathered, please review the tool call results for the answer."
    source = ""
    
    return {
        "answer": answer,
        "source": source,
        "tool_calls": tool_calls_log,
    }


def extract_source(answer: str) -> str:
    """
    Try to extract a source reference from the answer.
    
    Looks for patterns like wiki/filename.md#section or wiki/filename.md
    
    Args:
        answer: The LLM's answer text
        
    Returns:
        Source reference string, or empty string if not found
    """
    import re
    
    # Look for wiki file references with anchors
    pattern = r'wiki/[\w\-/]+\.md(?:#[\w\-]+)?'
    match = re.search(pattern, answer)
    
    if match:
        return match.group(0)
    
    return ""


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Error: No question provided.", file=sys.stderr)
        print("Usage: uv run agent.py \"Your question\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    print(f"Question: {question}", file=sys.stderr)

    config = load_config()
    print(f"Using model: {config['model']}", file=sys.stderr)

    result = run_agentic_loop(question, config)

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
