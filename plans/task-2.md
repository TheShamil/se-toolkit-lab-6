# Task 2 Plan: The Documentation Agent

## Overview

Transform the chatbot from Task 1 into an **agent** with tools. The agent will use `read_file` and `list_files` tools to navigate the project wiki and answer questions with source references.

## Agentic Loop Architecture

### Loop Flow

```
1. Send user question + tool definitions to LLM
2. Parse LLM response
   ├─ If tool_calls present → execute tools → append results → go to step 1
   └─ If text answer → extract answer + source → output JSON → exit
3. Maximum 10 iterations (tool call limit)
```

### Message Format

Messages will follow the OpenAI chat format with tool support:

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": question},
    # After tool calls:
    {"role": "assistant", "content": None, "tool_calls": [...]},
    {"role": "tool", "tool_call_id": "...", "content": tool_result},
]
```

## Tool Definitions

### `read_file`

**Purpose:** Read a file from the project repository.

**Schema:**
```json
{
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
```

**Implementation:**
- Use `Path` to resolve the file path
- Check for path traversal attacks (`../`)
- Verify the resolved path is within project root
- Return file contents or error message

### `list_files`

**Purpose:** List files and directories at a given path.

**Schema:**
```json
{
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
```

**Implementation:**
- Use `Path.iterdir()` to list entries
- Check for path traversal attacks
- Verify the resolved path is within project root
- Return newline-separated list of entry names

## Path Security

To prevent directory traversal attacks:

```python
def safe_path(relative_path: str, project_root: Path) -> Path:
    """Resolve and validate a relative path is within project root."""
    # Reject paths with ..
    if ".." in relative_path:
        raise ValueError("Path traversal not allowed")
    
    # Resolve the full path
    full_path = (project_root / relative_path).resolve()
    
    # Ensure it's within project root
    if not str(full_path).startswith(str(project_root.resolve())):
        raise ValueError("Path outside project root not allowed")
    
    return full_path
```

## System Prompt

The system prompt will instruct the LLM to:

1. Use `list_files` to discover wiki directory structure
2. Use `read_file` to read relevant files
3. Always include a source reference in the answer
4. Be concise and accurate

Example:
```
You are a documentation assistant. You have access to two tools:
- list_files: List files in a directory
- read_file: Read contents of a file

When answering questions:
1. First explore the wiki structure using list_files
2. Read relevant files using read_file
3. Provide a concise answer with the source file path and section
4. Format the source as: wiki/filename.md#section-anchor

Always use tools to find accurate answers - do not rely on your training data.
```

## Output Format

```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "..."
    }
  ]
}
```

## Implementation Steps

1. **Define tool schemas** - JSON schemas for `read_file` and `list_files`
2. **Implement tool functions** - Python functions with path security
3. **Update LLM call** - Include tool definitions in API request
4. **Parse tool calls** - Extract tool calls from LLM response
5. **Execute tools** - Run tools and capture results
6. **Build agentic loop** - Iterate until final answer or max calls
7. **Extract source** - Parse LLM answer to extract source reference
8. **Format output** - Include `source` and `tool_calls` in JSON output

## Test Strategy

Two regression tests:

1. **Test merge conflict question:**
   - Question: `"How do you resolve a merge conflict?"`
   - Expected: `read_file` in tool_calls, `wiki/git-workflow.md` in source

2. **Test wiki listing question:**
   - Question: `"What files are in the wiki?"`
   - Expected: `list_files` in tool_calls

## Files to Modify/Create

1. `plans/task-2.md` – this plan
2. `agent.py` – add tools and agentic loop
3. `AGENT.md` – document tools and loop
4. `tests/test_agent.py` – add 2 more tests
