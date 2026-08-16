from pathlib import Path

from bindery.ds import loader
from bindery.lint.pptx import lint
from bindery.render.pptx import render

REPO_ROOT = Path(__file__).resolve().parent.parent


def _composition(*blocks):
    return {
        "schema": "bindery/v1", "design_system": "editorial@1.0.0",
        "target": "pptx", "blocks": list(blocks),
    }


def test_editorial_loads_and_validates():
    ds = loader.load("editorial", root=REPO_ROOT / "design-systems")
    assert ds.name == "editorial"
    assert loader.validate(ds) == []


def test_editorial_renders_all_components_with_no_lint_violations(tmp_path):
    ds = loader.load("editorial", root=REPO_ROOT / "design-systems")
    composition = _composition(
        {"component": "title", "props": {
            "eyebrow": "Q3 2026", "headline": "Enrollment up 12%, cost per member flat",
            "accent": "secondary",
        }},
        {"component": "stat-trio", "props": {"stats": [
            {"value": "142,300", "label": "Members enrolled", "delta": "+12%"},
            {"value": "$412", "label": "Cost per member", "delta": "0%"},
            {"value": "94.2%", "label": "Retention", "delta": "+1.4pt"},
        ]}},
        {"component": "bullet-list", "props": {
            "heading": "Key drivers",
            "items": ["New employer group onboarded in July", "Retention held churn flat"],
        }},
        {"component": "image-callout", "props": {
            "asset": "growth-chart.png", "caption": "Enrollment trend, last 4 quarters",
            "accent": "secondary",
        }},
    )
    out = tmp_path / "deck.pptx"
    result = render(composition, ds, out)
    assert result.blocks_rendered == 4
    assert lint(out, ds) == []
