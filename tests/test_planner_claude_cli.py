import json
import subprocess

import pytest

from bindery.ds.loader import load
from bindery.planner.claude_cli import ClaudeCliConfig, ClaudeCliPlanner
from bindery.planner.errors import PlannerError


def _envelope(structured_output, is_error=False, stop_reason="tool_use"):
    return json.dumps(
        {
            "is_error": is_error,
            "stop_reason": stop_reason,
            "result": json.dumps(structured_output),
            "structured_output": structured_output,
        }
    )


def _composition(ds_spec):
    return {
        "schema": "bindery/v1", "design_system": ds_spec, "target": "pptx",
        "blocks": [{"component": "title", "props": {"headline": "Hi"}}],
    }


def test_plan_success(ds_root, monkeypatch):
    ds = load("reference@1.0.0", root=ds_root)

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            cmd, 0, stdout=_envelope(_composition("reference@1.0.0")), stderr=""
        )

    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/claude")
    monkeypatch.setattr("subprocess.run", fake_run)

    planner = ClaudeCliPlanner(ClaudeCliConfig())
    result = planner.plan("a brief", ds, "pptx")
    assert result["design_system"] == "reference@1.0.0"


def test_binary_not_found_raises(ds_root, monkeypatch):
    ds = load("reference@1.0.0", root=ds_root)
    monkeypatch.setattr("shutil.which", lambda x: None)

    planner = ClaudeCliPlanner(ClaudeCliConfig())
    with pytest.raises(PlannerError, match="not found on PATH"):
        planner.plan("a brief", ds, "pptx")


def test_nonzero_exit_raises(ds_root, monkeypatch):
    ds = load("reference@1.0.0", root=ds_root)

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Not logged in")

    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/claude")
    monkeypatch.setattr("subprocess.run", fake_run)

    planner = ClaudeCliPlanner(ClaudeCliConfig())
    with pytest.raises(PlannerError, match="Not logged in"):
        planner.plan("a brief", ds, "pptx")


def test_stringified_blocks_raises(ds_root, monkeypatch):
    """Regression test for the shallow-merge bug: if blocks ever comes back
    as a string instead of a list, fail loudly rather than pass a broken
    composition downstream."""
    ds = load("reference@1.0.0", root=ds_root)
    bad = _composition("reference@1.0.0")
    bad["blocks"] = json.dumps(bad["blocks"])

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 0, stdout=_envelope(bad), stderr="")

    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/claude")
    monkeypatch.setattr("subprocess.run", fake_run)

    planner = ClaudeCliPlanner(ClaudeCliConfig())
    with pytest.raises(PlannerError, match="not a JSON array"):
        planner.plan("a brief", ds, "pptx")


def test_no_structured_output_raises(ds_root, monkeypatch):
    ds = load("reference@1.0.0", root=ds_root)

    def fake_run(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(
            cmd, 0,
            stdout=json.dumps({"is_error": False, "stop_reason": "end_turn", "result": "no tool call"}),
            stderr="",
        )

    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/claude")
    monkeypatch.setattr("subprocess.run", fake_run)

    planner = ClaudeCliPlanner(ClaudeCliConfig())
    with pytest.raises(PlannerError, match="no structured_output"):
        planner.plan("a brief", ds, "pptx")
