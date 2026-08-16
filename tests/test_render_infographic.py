import pytest

from bindery.ds import loader
from bindery.render.errors import CompositionError
from bindery.render.infographic import render


@pytest.fixture
def ds(ds_root):
    return loader.load("reference", root=ds_root)


def _composition(*blocks):
    return {
        "schema": "bindery/v1", "design_system": "reference@1.0.0",
        "target": "infographic", "blocks": list(blocks),
    }


def test_render_title_and_stat_callout(ds, tmp_path):
    composition = _composition(
        {"component": "title", "props": {"headline": "Q3 update", "eyebrow": "fy26"}},
        {"component": "stat-callout", "props": {"value": "142,300", "label": "Members"}},
    )
    result = render(composition, ds, tmp_path / "out.svg")
    assert result.path.exists()
    assert result.blocks_rendered == 2

    svg = result.path.read_text()
    assert "<svg" in svg
    assert "Q3 update" in svg
    assert "142,300" in svg

    png_path = result.path.with_suffix(".png")
    assert png_path.exists()
    assert png_path.stat().st_size > 0


def test_blocks_stack_without_overlap(ds, tmp_path):
    composition = _composition(
        {"component": "title", "props": {"headline": "A"}},
        {"component": "stat-callout", "props": {"value": "1", "label": "B"}},
    )
    result = render(composition, ds, tmp_path / "out.svg")
    svg = result.path.read_text()
    # two distinct, non-zero translate y-offsets -> blocks didn't overlap at (x, same-y)
    import re
    ys = [int(m) for m in re.findall(r"translate\(\d+,(\d+)\)", svg)]
    assert len(ys) == 2
    assert ys[1] > ys[0]


def test_invalid_composition_raises(ds, tmp_path):
    composition = _composition({"component": "nonexistent", "props": {}})
    with pytest.raises(CompositionError):
        render(composition, ds, tmp_path / "out.svg")
