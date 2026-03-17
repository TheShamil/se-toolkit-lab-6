"""Regression tests for agent.py."""

import json
import subprocess
import sys
from pathlib import Path


def run_agent(question: str) -> dict:
    """Helper to run agent.py and parse JSON output."""
    project_root = Path(__file__).parent.parent
    agent_path = project_root / "agent.py"

    result = subprocess.run(
        ["uv", "run", str(agent_path), question],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=120,
    )

    assert result.returncode == 0, f"Agent failed with: {result.stderr}"

    # Parse stdout as JSON (last line, since debug output goes to stderr)
    stdout_lines = result.stdout.strip().split("\n")
    json_line = stdout_lines[-1]

    try:
        return json.loads(json_line)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON output: {json_line}") from e


def test_agent_outputs_valid_json():
    """Test that agent.py outputs valid JSON with required fields."""
    output = run_agent("What is 2 + 2?")

    # Check required fields
    assert "answer" in output, "Missing 'answer' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Check that answer is non-empty
    assert output["answer"], "Answer field is empty"

    print(f"✓ Test passed. Output: {output}")


def test_merge_conflict_question():
    """Test that merge conflict question uses read_file and returns wiki source."""
    output = run_agent("How do you resolve a merge conflict?")

    # Check required fields
    assert "answer" in output, "Missing 'answer' field"
    assert "source" in output, "Missing 'source' field"
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Check that at least one tool call used read_file
    tools_used = [tc.get("tool") for tc in output["tool_calls"]]
    assert "read_file" in tools_used, f"Expected read_file in tool_calls, got: {tools_used}"

    # Check that source contains wiki/git reference
    assert "wiki/" in output["source"].lower() or "wiki/" in output["answer"].lower(), \
        f"Expected wiki reference in source or answer, got source: {output['source']}"

    print(f"✓ Test passed. Source: {output['source']}")


def test_wiki_list_files_question():
    """Test that wiki listing question uses list_files tool."""
    output = run_agent("What files are in the wiki?")

    # Check required fields
    assert "answer" in output, "Missing 'answer' field"
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Check that at least one tool call used list_files
    tools_used = [tc.get("tool") for tc in output["tool_calls"]]
    assert "list_files" in tools_used, f"Expected list_files in tool_calls, got: {tools_used}"

    print(f"✓ Test passed. Tools used: {tools_used}")


def test_backend_framework_question():
    """Test that backend framework question uses read_file to examine source code."""
    output = run_agent("What Python web framework does the backend use?")

    # Check required fields
    assert "answer" in output, "Missing 'answer' field"
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Check that at least one tool call used read_file
    tools_used = [tc.get("tool") for tc in output["tool_calls"]]
    assert "read_file" in tools_used, f"Expected read_file in tool_calls, got: {tools_used}"

    # Check that answer mentions FastAPI
    assert "fastapi" in output["answer"].lower(), f"Expected 'FastAPI' in answer, got: {output['answer']}"

    print(f"✓ Test passed. Framework: FastAPI")


def test_database_items_count_question():
    """Test that database count question uses query_api tool."""
    output = run_agent("How many items are in the database?")

    # Check required fields
    assert "answer" in output, "Missing 'answer' field"
    assert "tool_calls" in output, "Missing 'tool_calls' field"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Check that at least one tool call used query_api
    tools_used = [tc.get("tool") for tc in output["tool_calls"]]
    assert "query_api" in tools_used, f"Expected query_api in tool_calls, got: {tools_used}"

    # Check that answer contains a number
    import re
    numbers = re.findall(r'\d+', output["answer"])
    assert len(numbers) > 0, f"Expected a number in answer, got: {output['answer']}"

    print(f"✓ Test passed. Items count: {numbers[0]}")
