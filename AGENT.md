# Agent Documentation

## Overview

This agent is a CLI tool that connects to an LLM (Large Language Model) with **tools** to answer questions using project documentation, source code, and the live backend API. The agent can:
- Read files and list directories to find accurate answers from the project wiki
- Query the backend API to get real-time data and test system behavior
- Diagnose bugs by combining API error responses with source code analysis

## Architecture

### Components

1. **Environment Configuration**
   - `.env.agent.secret`: LLM credentials (`LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL`)
   - `.env.docker.secret`: Backend API credentials (`LMS_API_KEY`, `AGENT_API_BASE_URL`)

2. **LLM Client** (`agent.py`)
   - Uses `httpx` for HTTP requests
   - Connects to an OpenAI-compatible API endpoint (Qwen Code)
   - Implements the chat completions API with **function calling**

3. **Tools**
   - `read_file`: Read contents of a file from the project
   - `list_files`: List files and directories at a path
   - `query_api`: Call the backend LMS API with optional authentication

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
                                     │  - query_api   │
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

**LLM Configuration** (`.env.agent.secret`):

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | Your Qwen API key | `sk-...` |
| `LLM_API_BASE` | API base URL | `http://10.93.24.168:42005/v1` |
| `LLM_MODEL` | Model name | `qwen3-coder-plus` |

**Backend Configuration** (`.env.docker.secret`):

| Variable | Description | Example |
|----------|-------------|---------|
| `LMS_API_KEY` | Backend API key for `query_api` auth | `my-secret-api-key` |
| `AGENT_API_BASE_URL` | Base URL for backend API | `http://localhost:42002` |

> **Important:** The autochecker runs your agent with different LLM credentials and a different backend URL. All configuration must come from environment variables, not hardcoded values.

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

### `query_api`

Call the backend LMS API to query data or test endpoints.

**Parameters:**
- `method` (string): HTTP method (GET, POST, PUT, DELETE)
- `path` (string): API path (e.g., `/items/`, `/analytics/completion-rate?lab=lab-99`)
- `body` (string, optional): JSON request body for POST/PUT requests
- `authorize` (boolean, default: true): Whether to send the Authorization header

**Returns:** JSON string with `status_code` and `body`, or an error message.

**Authentication:** Uses `LMS_API_KEY` from environment variables via `Authorization: Bearer <key>` header. Set `authorize=false` to test unauthenticated access.

### Tool Schemas

Tools are defined as JSON schemas sent to the LLM:

```json
{
  "type": "function",
  "function": {
    "name": "query_api",
    "description": "Call the backend LMS API to query data or test endpoints...",
    "parameters": {
      "type": "object",
      "properties": {
        "method": {"type": "string", "description": "HTTP method"},
        "path": {"type": "string", "description": "API path"},
        "body": {"type": "string", "description": "Optional JSON body"},
        "authorize": {"type": "boolean", "description": "Send auth header (default: true)"}
      },
      "required": ["method", "path"]
    }
  }
}
```

## System Prompt

The system prompt instructs the LLM on how to use tools:

```
You are a documentation and system assistant for a software engineering lab. You have access to three tools:

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

When citing sources:
- For wiki files: use format wiki/filename.md#section-anchor
- For source code: use format backend/app/file.py or path/to/file.py

Always use your tools to find accurate answers - do not rely on your training data alone.
```

## Usage

### Basic Usage

```bash
uv run agent.py "Your question here"
```

### Examples

**Wiki lookup:**
```bash
$ uv run agent.py "How do you resolve a merge conflict?"
{"answer": "...", "source": "wiki/git-vscode.md#resolve-a-merge-conflict", "tool_calls": [...]}
```

**API data query:**
```bash
$ uv run agent.py "How many items are in the database?"
{"answer": "There are 44 items in the database.", "source": "", "tool_calls": [
  {"tool": "query_api", "args": {"method": "GET", "path": "/items/"}, "result": "..."}
]}
```

**Authentication testing:**
```bash
$ uv run agent.py "What status code without auth?"
{"answer": "The API returns 401 Unauthorized.", "source": "", "tool_calls": [
  {"tool": "query_api", "args": {"method": "GET", "path": "/items/", "authorize": false}, ...}
]}
```

### Output Format

```json
{
  "answer": "The LLM's response to your question",
  "source": "wiki/filename.md#section-anchor or backend/app/file.py",
  "tool_calls": [
    {
      "tool": "read_file|list_files|query_api",
      "args": {...},
      "result": "..."
    }
  ]
}
```

- `answer` (string): The LLM's response
- `source` (string): Reference to the source file/section (optional for API questions)
- `tool_calls` (array): All tool calls made during the agentic loop

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
4. **test_backend_framework_question**: Uses `read_file` to find FastAPI in source
5. **test_database_items_count_question**: Uses `query_api` to get item count

## Benchmark Evaluation

Run the local evaluation benchmark:

```bash
uv run run_eval.py
```

This runs 10 questions across all classes:
- Wiki lookup (branch protection, SSH connection)
- Source code analysis (framework, router modules)
- API data queries (item count, status codes)
- Bug diagnosis (division by zero, NoneType errors)
- Reasoning questions (request lifecycle, ETL idempotency)

### Final Score

**10/10 passed** on local evaluation.

> **Note:** The autochecker bot tests 10 additional hidden questions and may use LLM-based judging for open-ended answers. You need to pass a minimum threshold overall.

## Implementation Details

### Path Security

Tools validate paths to prevent directory traversal attacks:

```python
def safe_path(relative_path: str, project_root: Path) -> Path:
    """Resolve and validate a relative path is within project root."""
    if ".." in relative_path:
        raise ValueError("Path traversal not allowed")
    
    full_path = (project_root / relative_path).resolve()
    
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
      {"type": "function", "function": {...list_files schema...}},
      {"type": "function", "function": {...query_api schema...}}
    ],
    "temperature": 0.7
  }
```

### Dependencies

- `httpx`: HTTP client for API calls
- `python-dotenv`: Environment variable loading (included with `pydantic-settings`)

## Lessons Learned

1. **Tool descriptions matter**: Initially the LLM didn't use `authorize=false` for authentication questions. Adding explicit guidance in both the tool description and system prompt fixed this.

2. **Environment variable separation**: Keeping LLM config (`.env.agent.secret`) separate from backend config (`.env.docker.secret`) is crucial for the autochecker to inject its own credentials.

3. **OAuth token expiry**: The Qwen Code OAuth token can expire. Restarting the proxy (`docker compose restart`) refreshes the authentication.

4. **Database population**: The ETL pipeline (`POST /pipeline/sync`) must be run to populate the database before testing data-dependent questions.

5. **Error handling**: The `query_api` tool needs to handle both HTTP errors and JSON parsing errors gracefully to provide useful feedback to the LLM.

6. **Source extraction**: The regex for extracting source references from answers needed to handle both wiki files (`.md#anchor`) and source code paths (`backend/app/file.py`).

## Future Work

- Add more tools (run shell commands, search code, etc.)
- Improve source extraction with better regex patterns
- Handle large file content with chunking/truncation
- Add caching for repeated API calls
- Support streaming responses for long answers
