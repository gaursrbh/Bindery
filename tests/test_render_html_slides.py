import pytest

from bindery.ds import loader
from bindery.render.errors import CompositionError
from bindery.render.html_slides import render


@pytest.fixture
def ds(ds_root):
    return loader.load("reference", root=ds_root)


def _composition(*blocks):
    return {
        "schema": "bindery/v1", "design_system": "reference@1.0.0",
        "target": "html-slides", "blocks": list(blocks),
    }


def test_render_single_slide(ds, tmp_path):
    composition = _composition(
        {"component": "title", "props": {"headline": "Q3 board update", "eyebrow": "fy26"}},
        {"component": "stat-trio", "props": {"stats": [
            {"value": "142,300", "label": "Members", "delta": "+12%"},
            {"value": "$412", "label": "Cost/member"},
            {"value": "94.2%", "label": "Retention"},
        ]}},
    )
    result = render(composition, ds, tmp_path / "out.html")
    assert result.path.exists()
    assert result.blocks_rendered == 2
    html = result.path.read_text()
    assert "Q3 board update" in html
    assert html.count('class="slide"') == 1


def test_title_starts_new_slide(ds, tmp_path):
    composition = _composition(
        {"component": "title", "props": {"headline": "Slide one"}},
        {"component": "bullet-list", "props": {"items": ["a", "b"]}},
        {"component": "title", "props": {"headline": "Slide two"}},
        {"component": "bullet-list", "props": {"items": ["c", "d"]}},
    )
    result = render(composition, ds, tmp_path / "out.html")
    html = result.path.read_text()
    assert html.count('class="slide"') == 2
    assert "Slide one" in html and "Slide two" in html


def test_invalid_composition_raises(ds, tmp_path):
    composition = _composition({"component": "nonexistent", "props": {}})
    with pytest.raises(CompositionError):
        render(composition, ds, tmp_path / "out.html")


def test_self_contained_no_external_refs(ds, tmp_path):
    composition = _composition(
        {"component": "title", "props": {"headline": "Hi"}},
    )
    result = render(composition, ds, tmp_path / "out.html")
    html = result.path.read_text()
    assert 'src="http' not in html
    assert 'href="http' not in html
