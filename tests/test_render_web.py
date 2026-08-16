import pytest

from bindery.ds import loader
from bindery.ds.errors import DesignSystemError
from bindery.render.errors import CompositionError
from bindery.render.web import render


@pytest.fixture
def ds(ds_root_with_web):
    return loader.load("reference", root=ds_root_with_web)


def _composition(*blocks):
    return {
        "schema": "bindery/v1",
        "design_system": "reference@1.0.0",
        "target": "web",
        "blocks": list(blocks),
    }


def test_render_title(ds, tmp_path):
    composition = _composition(
        {"component": "title", "props": {"headline": "Q3 board update", "eyebrow": "quarterly"}}
    )
    result = render(composition, ds, tmp_path / "out.html")
    assert result.path.exists()
    assert result.blocks_rendered == 1
    html = result.path.read_text()
    assert "Q3 board update" in html
    assert 'src="' not in html and 'href="./' not in html  # self-contained


def test_render_stat_trio_and_nav_bar(ds, tmp_path):
    composition = _composition(
        {
            "component": "stat-trio",
            "props": {
                "stats": [
                    {"value": "$4.2M", "label": "Revenue", "delta": "+12%"},
                    {"value": "94%", "label": "Retention"},
                    {"value": "312", "label": "Customers"},
                ]
            },
        },
        {"component": "nav-bar", "props": {"links": [{"label": "Home", "href": "#home"}]}},
    )
    result = render(composition, ds, tmp_path / "out.html")
    html = result.path.read_text()
    assert "Revenue" in html
    assert "Home" in html


def test_missing_node_modules_raises(ds_root, tmp_path):
    ds = loader.load("reference", root=ds_root)  # no node_modules symlink
    composition = _composition({"component": "title", "props": {"headline": "x"}})
    with pytest.raises(DesignSystemError):
        render(composition, ds, tmp_path / "out.html")


def test_invalid_composition_raises(ds, tmp_path):
    composition = _composition({"component": "nonexistent", "props": {}})
    with pytest.raises(CompositionError):
        render(composition, ds, tmp_path / "out.html")
