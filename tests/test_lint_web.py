from bindery.ds import loader
from bindery.lint.web import lint
from bindery.render.web import render


def test_compliant_render_has_no_violations(ds_root_with_web, tmp_path):
    ds = loader.load("reference", root=ds_root_with_web)
    composition = {
        "schema": "bindery/v1", "design_system": "reference@1.0.0", "target": "web",
        "blocks": [{"component": "title", "props": {"headline": "Q3 update"}}],
    }
    out = tmp_path / "out.html"
    render(composition, ds, out)
    assert lint(out, ds) == []


def test_off_token_color_in_style_object_detected(tmp_path, ds_root):
    ds = loader.load("reference", root=ds_root)
    html = (
        "<html><body><script>"
        'function App(){return me.jsx("div",{style:{color:"#FF00FF"},children:"hi"})}'
        "</script></body></html>"
    )
    out = tmp_path / "bad.html"
    out.write_text(html)

    violations = lint(out, ds)
    assert any(v.kind == "color" and v.value == "#FF00FF" for v in violations)


def test_var_reference_not_flagged(tmp_path, ds_root):
    ds = loader.load("reference", root=ds_root)
    html = (
        "<html><body><script>"
        'function App(){return me.jsx("div",{style:{color:"var(--color-primary)"},children:"hi"})}'
        "</script></body></html>"
    )
    out = tmp_path / "good.html"
    out.write_text(html)
    assert lint(out, ds) == []
