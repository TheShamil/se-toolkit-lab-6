#!/usr/bin/env python3
"""
Agent CLI - Calls an LLM with tools to answer questions using project documentation and backend API.

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
    """Load configuration from environment files."""
    # Load LLM config from .env.agent.secret
    agent_env = Path(__file__).parent / ".env.agent.secret"
    load_dotenv(agent_env)
    
    # Load backend config from .env.docker.secret
    docker_env = Path(__file__).parent / ".env.docker.secret"
    load_dotenv(docker_env, override=False)

    config = {
        "api_key": os.getenv("LLM_API_KEY"),
        "api_base": os.getenv("LLM_API_BASE"),
        "model": os.getenv("LLM_MODEL"),
        "lms_api_key": os.getenv("LMS_API_KEY"),
        "agent_api_base_url": os.getenv("AGENT_API_BASE_URL", "http://localhost:42002"),
    }

    missing = [k for k in ["api_key", "api_base", "model", "lms_api_key"] if not config.get(k)]
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


def query_api_tool(method: str, path: str, body: str = None, authorize: bool = True, lms_api_key: str = None, api_base_url: str = None) -> str:
    """
    Call the backend LMS API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API path (e.g., '/items/', '/analytics/completion-rate')
        body: Optional JSON request body
        authorize: Whether to send the Authorization header (default: True)
        lms_api_key: API key for authentication
        api_base_url: Base URL of the backend API

    Returns:
        JSON string with status_code and body, or error message
    """
    url = f"{api_base_url}{path}"
    headers = {
        "Content-Type": "application/json",
    }
    
    # Only add Authorization header if authorize=True
    if authorize and lms_api_key:
        headers["Authorization"] = f"Bearer {lms_api_key}"

    try:
        print(f"  Executing query_api: {method} {url} (auth={authorize})", file=sys.stderr)

        with httpx.Client(timeout=30.0) as client:
            if method.upper() == "GET":
                response = client.get(url, headers=headers)
            elif method.upper() == "POST":
                data = json.loads(body) if body else {}
                response = client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                data = json.loads(body) if body else {}
                response = client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                return f"Error: Unknown method: {method}"

        result = {
            "status_code": response.status_code,
            "body": response.json() if response.content else None,
        }
        return json.dumps(result)
    except httpx.HTTPError as e:
        return f"Error: HTTP error - {e}"
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON response - {e}"
    except Exception as e:
        return f"Error: {e}"


# Tool definitions for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the project repository. Use this to examine source code, documentation, or configuration files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md', 'backend/app/main.py')"
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
            "description": "List files and directories in a directory. Use this to explore the project structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki', 'backend/app/routers')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the backend LMS API to query data or test endpoints. Use this for questions about current data (item counts, scores), system behavior (status codes, errors), or runtime information. The API usually requires authentication, but you can set authorize=false to test unauthenticated access.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, DELETE)"
                    },
                    "path": {
                        "type": "string",
                        "description": "API path (e.g., '/items/', '/analytics/completion-rate?lab=lab-99')"
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body for POST/PUT requests"
                    },
                    "authorize": {
                        "type": "boolean",
                        "description": "Whether to send the Authorization header (default: true). Set to false to test unauthenticated access."
                    }
                },
                "required": ["method", "path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a documentation and system assistant for a software engineering lab. You have access to three tools:

1. list_files - List files and directories in a directory
2. read_file - Read the contents of a file
3. query_api - Call the backend LMS API to query data or test endpoints

Tool selection guide:
- Use list_files and read_file for:
  - Questions about project documentation in the wiki/ directory
  - Questions about source code structure or implementation
  - Questions about configuration files (docker-compose.yml, Dockerfile, etc.)

- Use query_api for:
  - Questions about current data (how many items, what scores, etc.)
  - Questions about system behavior (what status code, what error, etc.)
  - Questions that require querying the live running API
  - To test authentication: use authorize=false to check what happens without credentials

When answering questions:
1. Choose the right tool(s) based on the question type
2. For wiki/documentation questions: explore with list_files, then read with read_file
3. For data/system questions: use query_api to get real-time information
4. For code questions: use read_file to examine the relevant source files
5. For questions about unauthenticated access: use query_api with authorize=false
6. Provide accurate answers based on what you find

When citing sources (IMPORTANT):
- ALWAYS include a source reference in your answer when you read a file
- For wiki files: write "Source: wiki/filename.md#section-anchor"
- For source code: write "Source: backend/app/routers/analytics.py" (include the full path)
- For configuration: write "Source: docker-compose.yml"
- The section anchor is the lowercase version of the heading with spaces replaced by hyphens

Always use your tools to find accurate answers - do not rely on your training data alone.
"""


def execute_tool(tool_name: str, args: dict, project_root: Path, config: dict) -> str:
    """
    Execute a tool and return the result.
    
    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool
        project_root: The project root directory
        config: Configuration dict with API details
        
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
    elif tool_name == "query_api":
        method = args.get("method", "GET")
        path = args.get("path", "")
        body = args.get("body")
        authorize = args.get("authorize", True)  # Default to True
        return query_api_tool(
            method=method,
            path=path,
            body=body,
            authorize=authorize,
            lms_api_key=config["lms_api_key"],
            api_base_url=config["agent_api_base_url"],
        )
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
            answer = message.get("content") or ""
            
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
            
            result = execute_tool(tool_name, tool_args, project_root, config)
            
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

    Looks for patterns like wiki/filename.md#section or backend/app/file.py

    Args:
        answer: The LLM's answer text

    Returns:
        Source reference string, or empty string if not found
    """
    import re

    # Look for wiki file references with anchors
    pattern = r'(?:wiki|backend|docker-compose\.yml|Dockerfile|pyproject\.toml)/[\w\-/.]+\.(?:md|py|yml|yaml)(?:#[\w\-]+)?'
    match = re.search(pattern, answer)

    if match:
        return match.group(0)

    # Fallback: look for any path-like pattern
    pattern2 = r'backend/[\w\-/]+\.py'
    match2 = re.search(pattern2, answer)
    if match2:
        return match2.group(0)

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
    print(f"Backend API: {config['agent_api_base_url']}", file=sys.stderr)

    result = run_agentic_loop(question, config)

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
