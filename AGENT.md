# Agent Documentation

## Overview

This agent is a CLI tool that connects to an LLM (Large Language Model) with **tools** to answer questions using project documentation. The agent can read files and list directories to find accurate answers from the project wiki.

## Architecture

### Components

1. **Environment Configuration** (`.env.agent.secret`)
   - Stores LLM credentials and configuration
   - Uses `python-dotenv` to load variables at runtime

2. **LLM Client** (`agent.py`)
   - Uses `httpx` for HTTP requests
   - Connects to an OpenAI-compatible API endpoint
   - Implements the chat completions API with **function calling**

3. **Tools**
   - `read_file`: Read contents of a file from the project
   - `list_files`: List files and directories at a path

4. **Agentic Loop**
   - Iteratively calls LLM, executes tools, and feeds results back
   - Maximum 10 tool calls per question

5. **CLI Interface**
   - Accepts a question as the first command-line argument
   - Outputs structured JSON to stdout
   - Sends all debug/logging output to stderr

### Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   CLI Arg   │ ──→ │  Load Config │ ──→ │ Agentic Loop │ ──→ │ Output JSON  │
│  (question) │     │  (.env file) │     │ (LLM + Tools)│     │ (stdout)     │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                              │
                                              ▼
                                     ┌────────────────┐
                                     │  Tools:        │
                                     │  - read_file   │
                                     │  - list_files  │
                                     └────────────────┘
```

### Agentic Loop

The agentic loop enables the LLM to reason and act iteratively:

```
1. Send user question + tool definitions to LLM
2. Parse LLM response
   ├─ If tool_calls present:
   │   ├─ Execute each tool
   │   ├─ Append results as "tool" messages
   │   └─ Go to step 1 (with updated messages)
   └─ If text answer (no tool calls):
       ├─ Extract answer and source
       └─ Output JSON and exit
3. Maximum 10 iterations (tool call limit)
```

## LLM Provider

- **Provider**: Qwen Code API (self-hosted on VM)
- **Model**: `qwen3-coder-plus`
- **API Compatibility**: OpenAI-compatible chat completions API with function calling
- **Endpoint**: Configured via `LLM_API_BASE` environment variable

### Why Qwen Code?

- 1000 free requests per day
- Works from Russia
- No credit card required
- Strong tool-calling capabilities

## Configuration

### Environment Variables

Create `.env.agent.secret` from `.env.agent.example`:

```bash
cp .env.agent.example .env.agent.secret
```

Required variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | Your Qwen API key | `sk-...` |
| `LLM_API_BASE` | API base URL | `http://10.93.24.168:42005/v1` |
| `LLM_MODEL` | Model name | `qwen3-coder-plus` |

## Tools

### `read_file`

Read the contents of a file from the project repository.

**Parameters:**
- `path` (string): Relative path from project root (e.g., `wiki/git-workflow.md`)

**Returns:** File contents as a string, or an error message.

**Security:** Rejects paths with `..` traversal and paths outside project root.

### `list_files`

List files and directories at a given path.

**Parameters:**
- `path` (string): Relative directory path from project root (e.g., `wiki`)

**Returns:** Newline-separated list of entry names, or an error message.

**Security:** Rejects paths with `..` traversal and paths outside project root.

### Tool Schemas

Tools are defined as JSON schemas sent to the LLM:

```json
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
          "description": "Relative path from project root"
        }
      },
      "required": ["path"]
    }
  }
}
```

## System Prompt

The system prompt instructs the LLM on how to use tools:

```
You are a documentation assistant for a software engineering lab. You have access to two tools:

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
```

## Usage

### Basic Usage

```bash
uv run agent.py "Your question here"
```

### Example

```bash
$ uv run agent.py "How do you resolve a merge conflict?"
Question: How do you resolve a merge conflict?
Using model: qwen3-coder-plus

--- Iteration 1 ---
Calling LLM at http://10.93.24.168:42005/v1/chat/completions...
LLM requested 1 tool call(s)
  Executing list_files: wiki

--- Iteration 2 ---
Calling LLM at http://10.93.24.168:42005/v1/chat/completions...
LLM requested 1 tool call(s)
  Executing read_file: wiki/git-vscode.md

--- Iteration 3 ---
Calling LLM at http://10.93.24.168:42005/v1/chat/completions...
LLM provided final answer (no tool calls)
{"answer": "...", "source": "wiki/git-vscode.md#resolve-a-merge-conflict", "tool_calls": [...]}
```

### Output Format

The agent outputs a single JSON line to stdout:

```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-vscode.md#resolve-a-merge-conflict",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "api.md\nbackend.md\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-vscode.md"},
      "result": "# Git in VS Code\n\n..."
    }
  ]
}
```

- `answer` (string): The LLM's response to your question
- `source` (string): Reference to the wiki section that answers the question (e.g., `wiki/git-workflow.md#resolving-merge-conflicts`)
- `tool_calls` (array): All tool calls made during the agentic loop. Each entry has:
  - `tool` (string): Tool name (`read_file` or `list_files`)
  - `args` (object): Arguments passed to the tool
  - `result` (string): Tool output

### Exit Codes

- `0`: Success
- `1`: Error (missing argument, missing config, API error)

## Testing

Run all regression tests:

```bash
uv run pytest tests/test_agent.py -v
```

Tests verify:
1. **test_agent_outputs_valid_json**: Basic JSON output with required fields
2. **test_merge_conflict_question**: Uses `read_file` and returns wiki source
3. **test_wiki_list_files_question**: Uses `list_files` tool

## Implementation Details

### Path Security

Tools validate paths to prevent directory traversal attacks:

```python
def safe_path(relative_path: str, project_root: Path) -> Path:
    """Resolve and validate a relative path is within project root."""
    # Reject paths with ..
    if ".." in relative_path:
        raise ValueError("Path traversal not allowed")
    
    # Resolve the full path
    full_path = (project_root / relative_path).resolve()
    
    # Ensure it's within project root
    if not str(full_path).startswith(str(project_root)):
        raise ValueError("Path outside project root not allowed")
    
    return full_path
```

### HTTP Request with Tool Calling

```python
POST {LLM_API_BASE}/chat/completions
Headers:
  Authorization: Bearer {LLM_API_KEY}
  Content-Type: application/json
Body:
  {
    "model": "qwen3-coder-plus",
    "messages": [...],
    "tools": [
      {"type": "function", "function": {...read_file schema...}},
      {"type": "function", "function": {...list_files schema...}}
    ],
    "temperature": 0.7
  }
```

### Dependencies

- `httpx`: HTTP client for API calls
- `python-dotenv`: Environment variable loading (included with `pydantic-settings`)

## Future Work (Task 3)

- Add more tools (query backend API, run commands, etc.)
- Expand system prompt with domain knowledge
- Improve source extraction
- Handle edge cases (empty files, large directories)
