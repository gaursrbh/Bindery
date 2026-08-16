import yaml

import bindery.cli as cli
from bindery.planner.errors import PlannerError
from bindery.render.errors import CompositionError, RenderError
from bindery.render.pptx import RenderResult


def _write_brief(path, **overrides):
    doc = {
        "intent": "Q3 update",
        "target": "pptx",
        "design_system": "reference@1.0.0",
        "constraints": {"max_slides": 3},
    }
    doc.update(overrides)
    path.write_text(yaml.safe_dump(doc))


def test_plan_success(ds_root, tmp_path, monkeypatch, capsys):
    brief_path = tmp_path / "brief.yaml"
    _write_brief(brief_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    fake_result = RenderResult(path=out_dir / "brief.pptx", duration_ms=1, blocks_rendered=1)
    monkeypatch.setattr(cli, "plan_with_repair", lambda *a, **k: fake_result)

    code = cli.main(
        ["plan", str(brief_path), "--out", str(out_dir), "--ds-root", str(ds_root)]
    )
    assert code == 0
    assert str(fake_result.path) in capsys.readouterr().out


def test_plan_ds_flag_overrides_brief(ds_root, tmp_path, monkeypatch):
    brief_path = tmp_path / "brief.yaml"
    _write_brief(brief_path, design_system="nonexistent@9.9.9")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    captured = {}

    def fake_plan_with_repair(brief, ds, target, planner, out_path, **kw):
        captured["ds_spec"] = ds.spec
        return RenderResult(path=out_path, duration_ms=1, blocks_rendered=1)

    monkeypatch.setattr(cli, "plan_with_repair", fake_plan_with_repair)

    code = cli.main(
        [
            "plan", str(brief_path),
            "--ds", "reference@1.0.0",
            "--out", str(out_dir),
            "--ds-root", str(ds_root),
        ]
    )
    assert code == 0
    assert captured["ds_spec"] == "reference@1.0.0"


def test_plan_missing_ds_exits_2(tmp_path):
    brief_path = tmp_path / "brief.yaml"
    _write_brief(brief_path, design_system=None)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    code = cli.main(["plan", str(brief_path), "--out", str(out_dir)])
    assert code == 2


def test_plan_exits_5_on_planner_error(ds_root, tmp_path, monkeypatch):
    brief_path = tmp_path / "brief.yaml"
    _write_brief(brief_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    def raise_planner_error(*a, **k):
        raise PlannerError("could not reach Ollama")

    monkeypatch.setattr(cli, "plan_with_repair", raise_planner_error)

    code = cli.main(
        ["plan", str(brief_path), "--out", str(out_dir), "--ds-root", str(ds_root)]
    )
    assert code == 5


def test_plan_exits_4_on_render_error_exhausted(ds_root, tmp_path, monkeypatch):
    brief_path = tmp_path / "brief.yaml"
    _write_brief(brief_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    def raise_render_error(*a, **k):
        raise RenderError(0, "title", "overflow (exhausted 3 repair attempts)")

    monkeypatch.setattr(cli, "plan_with_repair", raise_render_error)

    code = cli.main(
        ["plan", str(brief_path), "--out", str(out_dir), "--ds-root", str(ds_root)]
    )
    assert code == 4


def test_plan_exits_3_on_composition_error(ds_root, tmp_path, monkeypatch):
    brief_path = tmp_path / "brief.yaml"
    _write_brief(brief_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    def raise_composition_error(*a, **k):
        raise CompositionError("composition invalid")

    monkeypatch.setattr(cli, "plan_with_repair", raise_composition_error)

    code = cli.main(
        ["plan", str(brief_path), "--out", str(out_dir), "--ds-root", str(ds_root)]
    )
    assert code == 3
