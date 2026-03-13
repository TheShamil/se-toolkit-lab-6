# Task 1 Plan: Call an LLM from Code

## LLM Provider and Model

- **Provider**: Qwen Code API (self-hosted on VM)
- **Model**: `qwen3-coder-plus`
- **Endpoint**: `http://10.93.24.168:42005/v1` (OpenAI-compatible)
- **Authentication**: API key stored in `.env.agent.secret`

## Agent Structure

### Components

1. **Environment Loading**
   - Use `python-dotenv` to load variables from `.env.agent.secret`
   - Required variables: `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL`

2. **LLM Client**
   - Use the `openai` Python SDK (works with any OpenAI-compatible endpoint)
   - Configure with custom `base_url` pointing to Qwen Code API
   - Use chat completions API

3. **CLI Interface**
   - Accept question as first command-line argument via `sys.argv`
   - Exit with error if no argument provided

4. **Prompt Design**
   - System prompt: instruct the model to respond concisely
   - User message: the question from command line

5. **Output Formatting**
   - Parse LLM response and output JSON: `{"answer": "...", "tool_calls": []}`
   - All debug output to `stderr`
   - Only valid JSON to `stdout`

### Data Flow

```
CLI argument → Load env vars → Create OpenAI client → Call LLM → Parse response → Output JSON
```

## Error Handling

- Missing command-line argument → exit with error message to stderr
- Missing environment variables → exit with descriptive error
- API timeout/error → exit with error message to stderr
- Ensure exit code 0 only on success

## Test Strategy

- Create `tests/test_agent.py` using pytest
- Run `agent.py` as subprocess with a simple question
- Parse stdout as JSON
- Assert `answer` and `tool_calls` fields exist
- Assert `tool_calls` is an empty list

## Files to Create

1. `plans/task-1.md` – this plan
2. `agent.py` – the main agent CLI
3. `AGENT.md` – documentation
4. `tests/test_agent.py` – regression test
