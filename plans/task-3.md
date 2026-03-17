# Task 3 Plan: The System Agent

## Overview

Add a `query_api` tool to the agent so it can query the deployed backend API. This enables answering data-dependent questions (item counts, scores) and system facts (framework, status codes) that cannot be found in documentation.

## LLM Configuration from Environment Variables

The agent must read all LLM configuration from environment variables (not hardcoded):

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |

## Backend Configuration from Environment Variables

| Variable | Purpose | Source |
|----------|---------|--------|
| `LMS_API_KEY` | Backend API key for `query_api` auth | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Base URL for backend API (optional) | `.env.docker.secret` or default |

Default for `AGENT_API_BASE_URL`: `http://localhost:42002` (Caddy proxy port)

## New Tool: `query_api`

### Schema

```json
{
  "type": "function",
  "function": {
    "name": "query_api",
    "description": "Call the backend LMS API to query data or test endpoints",
    "parameters": {
      "type": "object",
      "properties": {
        "method": {
          "type": "string",
          "description": "HTTP method (GET, POST, PUT, DELETE)"
        },
        "path": {
          "type": "string",
          "description": "API path (e.g., '/items/', '/analytics/completion-rate')"
        },
        "body": {
          "type": "string",
          "description": "Optional JSON request body (for POST/PUT)"
        }
      },
      "required": ["method", "path"]
    }
  }
}
```

### Implementation

```python
def query_api_tool(method: str, path: str, body: str = None) -> str:
    """Call the backend API and return response."""
    url = f"{AGENT_API_BASE_URL}{path}"
    headers = {
        "X-API-Key": LMS_API_KEY,  # or Authorization header
        "Content-Type": "application/json"
    }
    
    # Make HTTP request with httpx
    # Return JSON string with status_code and body
```

### Authentication

The backend uses API key authentication via `X-API-Key` header (need to verify exact header name from `auth.py`).

## System Prompt Update

Update the system prompt to guide the LLM on when to use each tool:

```
You are a documentation and system assistant. You have three types of tools:

1. Wiki tools (list_files, read_file) - For questions about project documentation, 
   workflows, or guidelines stored in the wiki/ directory.

2. API tool (query_api) - For questions about:
   - Current data in the system (item counts, scores, analytics)
   - System behavior (status codes, error responses)
   - Runtime information that requires querying the live API

When answering questions:
- For wiki/documentation questions: use list_files and read_file
- For data/system questions: use query_api
- For code questions: use read_file to examine source code

Always provide accurate answers based on the actual data or files you read.
```

## Agentic Loop

The agentic loop remains the same as Task 2:
1. Send question + tool definitions to LLM
2. If tool_calls present → execute tools → append results → repeat
3. If text answer → output JSON
4. Maximum 10 tool calls

## Output Format

```json
{
  "answer": "There are 120 items in the database.",
  "source": "",  // Optional for API questions
  "tool_calls": [
    {
      "tool": "query_api",
      "args": {"method": "GET", "path": "/items/"},
      "result": "{\"status_code\": 200, \"body\": {...}}"
    }
  ]
}
```

## Benchmark Evaluation

Run `run_eval.py` to test against 10 local questions:

| # | Question Type | Expected Tool |
|---|---------------|---------------|
| 0-1 | Wiki lookup | read_file |
| 2-3 | Source code lookup | read_file, list_files |
| 4-7 | API data queries | query_api, read_file |
| 8-9 | Reasoning (LLM judge) | read_file |

### Iteration Strategy

1. Run `run_eval.py` to get initial score
2. For each failure:
   - Check if wrong tool was used → improve system prompt
   - Check if tool returned error → fix tool implementation
   - Check if answer doesn't match keywords → adjust phrasing
3. Re-run until all 10 pass

## Files to Modify

1. `plans/task-3.md` – this plan
2. `agent.py` – add `query_api` tool, update config loading, update system prompt
3. `AGENT.md` – document `query_api`, lessons learned, final score
4. `tests/test_agent.py` – add 2 more tests for `query_api`

## Risk Mitigation

- **Hardcoding risk**: All config from env vars, not hardcoded
- **Timeout risk**: 60s timeout per question, max 10 tool calls
- **Auth risk**: Use correct header name from `auth.py`

## Benchmark Results

### Initial Run

**Score: 5/10 passed**

Failures:
1. **Question 6** (status code without auth): Agent returned 200 instead of 401 because `query_api` always sent auth header.

### Iteration 1

**Fix**: Added `authorize` parameter to `query_api` tool with default `true`. Updated tool description and system prompt to guide LLM to use `authorize=false` for authentication testing questions.

### Final Run

**Score: 10/10 passed** ✅

All questions passing:
- [x] Wiki: branch protection steps
- [x] Wiki: SSH connection steps
- [x] Source: FastAPI framework
- [x] Source: API router modules
- [x] API: Item count (44 items)
- [x] API: Status code without auth (401)
- [x] API + Source: Division by zero bug
- [x] API + Source: NoneType error bug
- [x] Reasoning: Request lifecycle (LLM judge)
- [x] Reasoning: ETL idempotency (LLM judge)
