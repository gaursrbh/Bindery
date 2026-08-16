from fastapi.testclient import TestClient

import bindery.server as server_module
from bindery.server import create_app


def _client(ds_root, tmp_path):
    out_dir = tmp_path / "out"
    app = create_app(out_dir, ds_root)
    return TestClient(app), out_dir


def test_list_design_systems(ds_root, tmp_path):
    client, _ = _client(ds_root, tmp_path)
    res = client.get("/design-systems")
    assert res.status_code == 200
    names = {d["name"] for d in res.json()}
    assert names == {"reference"}


def test_generate_and_list_artifacts(ds_root, tmp_path):
    client, out_dir = _client(ds_root, tmp_path)
    composition = {
        "schema": "bindery/v1", "design_system": "reference@1.0.0", "target": "pptx",
        "blocks": [{"component": "title", "props": {"headline": "Q3 update"}}],
    }
    res = client.post("/generate", json={"composition": composition, "ds": "reference@1.0.0"})
    assert res.status_code == 200
    artifact_id = res.json()["id"]

    res = client.get("/artifacts")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.get(f"/artifacts/{artifact_id}")
    assert res.status_code == 200
    assert res.json()["lock"]["design_system"] == "reference@1.0.0"

    res = client.get(f"/artifacts/{artifact_id}/file")
    assert res.status_code == 200
    assert res.content.startswith(b"PK")  # .pptx is a zip archive


def test_generate_invalid_composition_returns_422(ds_root, tmp_path):
    client, _ = _client(ds_root, tmp_path)
    composition = {
        "schema": "bindery/v1", "design_system": "reference@1.0.0", "target": "pptx",
        "blocks": [{"component": "nonexistent", "props": {}}],
    }
    res = client.post("/generate", json={"composition": composition, "ds": "reference@1.0.0"})
    assert res.status_code == 422


def test_rerender_via_api(ds_root, tmp_path):
    client, out_dir = _client(ds_root, tmp_path)
    composition = {
        "schema": "bindery/v1", "design_system": "reference@1.0.0", "target": "pptx",
        "blocks": [{"component": "title", "props": {"headline": "Q3 update"}}],
    }
    res = client.post("/generate", json={"composition": composition, "ds": "reference@1.0.0"})
    artifact_id = res.json()["id"]

    res = client.post(f"/artifacts/{artifact_id}/rerender")
    assert res.status_code == 200


def test_frontend_served(ds_root, tmp_path):
    client, _ = _client(ds_root, tmp_path)
    res = client.get("/")
    assert res.status_code == 200
    assert "Bindery" in res.text
    assert "claude-cli" in res.text  # planner selector present


def test_plan_with_claude_cli_planner(ds_root, tmp_path, monkeypatch):
    client, out_dir = _client(ds_root, tmp_path)

    class FakePlanner:
        def __init__(self, config):
            self.config = config

        def plan(self, brief, ds, target, *, repair=None):
            return {
                "schema": "bindery/v1", "design_system": ds.spec, "target": target,
                "blocks": [{"component": "title", "props": {"headline": "Q3 update"}}],
            }

    monkeypatch.setattr(server_module, "ClaudeCliPlanner", FakePlanner)

    res = client.post("/plan", json={
        "intent": "Q3 update", "target": "pptx",
        "design_system": "reference@1.0.0", "planner": "claude-cli",
    })
    assert res.status_code == 200
    assert res.json()["design_system"] == "reference@1.0.0"
