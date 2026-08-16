import json
import urllib.error

import pytest

from bindery.ds.loader import load
from bindery.planner.errors import PlannerError
from bindery.planner.ollama import OllamaPlanner, PlannerConfig


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _composition_json(ds_spec: str) -> str:
    return json.dumps(
        {
            "schema": "bindery/v1",
            "design_system": ds_spec,
            "target": "pptx",
            "blocks": [{"component": "title", "props": {"headline": "Hi"}}],
        }
    )


def test_plan_success(ds_root, monkeypatch):
    ds = load("reference@1.0.0", root=ds_root)

    def fake_urlopen(req, timeout):
        envelope = json.dumps({"response": _composition_json("reference@1.0.0")}).encode()
        return _FakeResponse(envelope)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    planner = OllamaPlanner(PlannerConfig())
    result = planner.plan("a brief", ds, "pptx")
    assert result["design_system"] == "reference@1.0.0"


def test_plan_raises_on_unreachable(ds_root, monkeypatch):
    ds = load("reference@1.0.0", root=ds_root)

    def fake_urlopen(req, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    planner = OllamaPlanner(PlannerConfig())
    with pytest.raises(PlannerError):
        planner.plan("a brief", ds, "pptx")


def test_plan_raises_on_non_json_response(ds_root, monkeypatch):
    ds = load("reference@1.0.0", root=ds_root)

    def fake_urlopen(req, timeout):
        return _FakeResponse(json.dumps({"response": "not json at all"}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    planner = OllamaPlanner(PlannerConfig())
    with pytest.raises(PlannerError):
        planner.plan("a brief", ds, "pptx")
