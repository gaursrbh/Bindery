from bindery.ds import loader
from bindery.lint.html_slides import lint
from bindery.render.html_slides import render


def test_compliant_render_has_no_violations(ds_root, tmp_path):
    ds = loader.load("reference", root=ds_root)
    composition = {
        "schema": "bindery/v1", "design_system": "reference@1.0.0", "target": "html-slides",
        "blocks": [{"component": "title", "props": {"headline": "Q3 update", "eyebrow": "fy26"}}],
    }
    out = tmp_path / "out.html"
    render(composition, ds, out)
    assert lint(out, ds) == []


def test_off_token_color_and_size_detected(ds_root, tmp_path):
    ds = loader.load("reference", root=ds_root)
    out = tmp_path / "bad.html"
    out.write_text('<div style="color:#FF00FF;font-size:99px;">hi</div>')

    violations = lint(out, ds)
    kinds = {v.kind for v in violations}
    assert "color" in kinds
    assert "font-size" in kinds


def test_var_reference_not_flagged(ds_root, tmp_path):
    ds = loader.load("reference", root=ds_root)
    out = tmp_path / "good.html"
    out.write_text('<div style="color:var(--color-primary);">hi</div>')
    assert lint(out, ds) == []
