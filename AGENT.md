# Agent Documentation

## Overview

This agent is a CLI tool that connects to an LLM (Large Language Model) to answer questions. It serves as the foundation for a more advanced agent with tools and agentic capabilities in later tasks.

## Architecture

### Components

1. **Environment Configuration** (`.env.agent.secret`)
   - Stores LLM credentials and configuration
   - Uses `python-dotenv` to load variables at runtime

2. **LLM Client** (`agent.py`)
   - Uses `httpx` for HTTP requests
   - Connects to an OpenAI-compatible API endpoint
   - Implements the chat completions API protocol

3. **CLI Interface**
   - Accepts a question as the first command-line argument
   - Outputs structured JSON to stdout
   - Sends all debug/logging output to stderr

### Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   CLI Arg   │ ──→ │  Load Config │ ──→ │  Call LLM   │ ──→ │  Output JSON │
│  (question) │     │  (.env file) │     │  (HTTP POST)│     │  (stdout)    │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

## LLM Provider

- **Provider**: Qwen Code API (self-hosted on VM)
- **Model**: `qwen3-coder-plus`
- **API Compatibility**: OpenAI-compatible chat completions API
- **Endpoint**: Configured via `LLM_API_BASE` environment variable

### Why Qwen Code?

- 1000 free requests per day
- Works from Russia
- No credit card required
- Strong tool-calling capabilities (for future tasks)

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

## Usage

### Basic Usage

```bash
uv run agent.py "Your question here"
```

### Example

```bash
$ uv run agent.py "What does REST stand for?"
Question: What does REST stand for?
Using model: qwen3-coder-plus
Calling LLM at http://10.93.24.168:42005/v1/chat/completions...
Received answer from LLM.
{"answer": "REST stands for **Representational State Transfer**.", "tool_calls": []}
```

### Output Format

The agent outputs a single JSON line to stdout:

```json
{
  "answer": "The LLM's response to your question",
  "tool_calls": []
}
```

- `answer` (string): The LLM's response
- `tool_calls` (array): Empty for Task 1, populated in Task 2+ when tools are added

### Exit Codes

- `0`: Success
- `1`: Error (missing argument, missing config, API error)

## Testing

Run the regression test:

```bash
uv run pytest tests/test_agent.py -v
```

The test verifies:
- The agent outputs valid JSON
- The `answer` field is present
- The `tool_calls` field is present and is an array

## Implementation Details

### HTTP Request

The agent makes a POST request to the LLM API:

```python
POST {LLM_API_BASE}/chat/completions
Headers:
  Authorization: Bearer {LLM_API_KEY}
  Content-Type: application/json
Body:
  {
    "model": "qwen3-coder-plus",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant..."},
      {"role": "user", "content": "Your question"}
    ],
    "temperature": 0.7
  }
```

### Dependencies

- `httpx`: HTTP client for API calls
- `python-dotenv`: Environment variable loading (included with `pydantic-settings`)

## Future Work (Tasks 2-3)

- Add tools (file operations, API queries, etc.)
- Implement agentic loop for multi-step reasoning
- Expand system prompt with domain knowledge
- Populate `tool_calls` with actual tool invocations
