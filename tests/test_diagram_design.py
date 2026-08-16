import json
from pathlib import Path

import pytest

from bindery import diagram_design as dd


def test_style_guide_from_tokens_maps_roles():
    tokens = json.loads(Path("design-systems/reference/tokens.json").read_text())
    guide = dd.style_guide_from_tokens(tokens)
    assert "`paper`: #FFFFFF" in guide
    assert "`ink`: #1A1A1A" in guide
    assert "`accent`: #C97A2B" in guide
    assert "Helvetica Neue" in guide
    assert "skip the first-time-setup onboarding gate" in guide


def test_generate_diagram_rejects_unknown_type(tmp_path):
    with pytest.raises(dd.DiagramDesignError):
        dd.generate_diagram("comic-strip", "x", {}, tmp_path)


def test_generate_diagram_happy_path(tmp_path, monkeypatch):
    def fake_fetch(rel_path, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f"# stub {rel_path}")

    monkeypatch.setattr(dd, "_fetch_skill_file", fake_fetch)

    def fake_run(cmd, cwd, capture_output, text, timeout):
        (Path(cwd) / "diagram.html").write_text(
            "<!doctype html><html><body><svg width='100' height='100'><circle r='1'/></svg>"
            "<!-- assumed defaults --></body></html>"
        )

        class Result:
            returncode = 0
            stdout = "{}"
            stderr = ""

        return Result()

    monkeypatch.setattr(dd.subprocess, "run", fake_run)

    result = dd.generate_diagram("venn", "two overlapping sets", {}, tmp_path)
    assert result.svg_path.exists()
    assert result.svg_path.read_text().startswith("<svg")
    assert result.html_path.exists()
    assert result.png_path.exists()


def test_generate_diagram_raises_when_no_html_written(tmp_path, monkeypatch):
    def fake_fetch(rel_path, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("stub")

    monkeypatch.setattr(dd, "_fetch_skill_file", fake_fetch)

    def fake_run(cmd, cwd, capture_output, text, timeout):
        class Result:
            returncode = 0
            stdout = "{}"
            stderr = ""

        return Result()

    monkeypatch.setattr(dd.subprocess, "run", fake_run)

    with pytest.raises(dd.DiagramDesignError):
        dd.generate_diagram("venn", "x", {}, tmp_path)
