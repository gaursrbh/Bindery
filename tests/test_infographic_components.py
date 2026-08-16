import pytest

from bindery.ds import loader
from bindery.render.infographic import render

CASES = {
    "linear-progression": {"steps": [
        {"label": "Discover", "detail": "Find the problem"},
        {"label": "Design", "detail": "Sketch the solution"},
    ]},
    "binary-comparison": {
        "left_label": "Before", "left_items": ["Manual process", "No visibility"],
        "right_label": "After", "right_items": ["Automated", "Real-time dashboard"],
    },
    "comparison-matrix": {
        "columns": ["Speed", "Cost"],
        "rows": [
            {"label": "Option A", "values": ["Fast", "$$"]},
            {"label": "Option B", "values": ["Slow", "$"]},
        ],
    },
    "hierarchical-layers": {"layers": [{"label": "Vision"}, {"label": "Execution"}]},
    "hub-spoke": {"hub": "Platform", "spokes": ["Billing", "Auth", "Search"]},
    "funnel": {"stages": [
        {"label": "Visitors", "value": "10,000"}, {"label": "Paid", "value": "300"},
    ]},
    "venn-diagram": {"left_label": "Design", "right_label": "Engineering", "overlap_label": "UX"},
    "circular-flow": {"stages": ["Plan", "Build", "Measure"]},
}


@pytest.fixture
def ds(ds_root):
    return loader.load("reference", root=ds_root)


@pytest.mark.parametrize("component,props", CASES.items())
def test_component_renders_valid_svg(ds, tmp_path, component, props):
    composition = {
        "schema": "bindery/v1", "design_system": "reference@1.0.0", "target": "infographic",
        "blocks": [{"component": component, "props": props}],
    }
    out = tmp_path / "out.svg"
    result = render(composition, ds, out)
    assert result.blocks_rendered == 1
    svg = out.read_text()
    assert svg.startswith("<svg")
    assert svg.strip().endswith("</svg>")
    png = out.with_suffix(".png")
    assert png.exists() and png.stat().st_size > 0


def test_all_eight_components_loaded(ds):
    for component in CASES:
        assert component in ds.layout_fns["infographic"]
