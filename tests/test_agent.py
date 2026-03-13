"""Regression tests for agent.py."""

import json
import subprocess
import sys
from pathlib import Path


def test_agent_outputs_valid_json():
    """Test that agent.py outputs valid JSON with required fields."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    agent_path = project_root / "agent.py"

    # Run agent.py with a simple question using uv run
    result = subprocess.run(
        ["uv", "run", str(agent_path), "What is 2 + 2?"],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    # Check exit code
    assert result.returncode == 0, f"Agent failed with: {result.stderr}"

    # Parse stdout as JSON (last line, since debug output goes to stderr)
    # Filter out any uv warnings that might appear
    stdout_lines = result.stdout.strip().split("\n")
    json_line = stdout_lines[-1]  # Last line should be the JSON output

    try:
        output = json.loads(json_line)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON output: {json_line}") from e

    # Check required fields
    assert "answer" in output, "Missing 'answer' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Check that answer is non-empty
    assert output["answer"], "Answer field is empty"

    print(f"✓ Test passed. Output: {output}")
