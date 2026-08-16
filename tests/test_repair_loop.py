from bindery.ds.loader import load
from bindery.planner.repair import plan_with_repair
from bindery.render.errors import RenderError


def _comp(ds_spec: str, headline: str) -> dict:
    return {
        "schema": "bindery/v1",
        "design_system": ds_spec,
        "target": "pptx",
        "blocks": [{"component": "title", "props": {"headline": headline}}],
    }


class _FlakyPlanner:
    """check_overflow is monkeypatched per-test to control pass/fail — the
    headline text here just needs to satisfy the schema (maxLength 90)."""

    def __init__(self, ds_spec):
        self.calls = 0
        self.ds_spec = ds_spec

    def plan(self, brief, ds, target, *, repair=None):
        self.calls += 1
        headline = "long headline that overflows" if repair is None else "short"
        return _comp(self.ds_spec, headline)


class _AlwaysFailsPlanner:
    def __init__(self, ds_spec):
        self.calls = 0
        self.ds_spec = ds_spec

    def plan(self, brief, ds, target, *, repair=None):
        self.calls += 1
        return _comp(self.ds_spec, "headline that always overflows")


def test_repair_loop_converges(ds_root, monkeypatch, tmp_path):
    import bindery.render.pptx as pptx_module

    def tiny_overflow(shape, font_family, block_index, prop):
        # force overflow exactly once via a call counter on the module
        tiny_overflow.n += 1
        if tiny_overflow.n == 1:
            raise RenderError(block_index, prop, "text overflows frame: needs 999pt, frame provides 1pt")

    tiny_overflow.n = 0
    monkeypatch.setattr(pptx_module, "check_overflow", tiny_overflow)

    ds = load("reference@1.0.0", root=ds_root)
    planner = _FlakyPlanner(ds.spec)
    out = tmp_path / "out.pptx"

    result, composition = plan_with_repair("brief", ds, "pptx", planner, out, max_attempts=3)
    assert result.path == out
    assert composition["blocks"][0]["props"]["headline"] == "short"
    assert planner.calls == 2


def test_repair_loop_exhausts_and_raises(ds_root, monkeypatch, tmp_path):
    import bindery.render.pptx as pptx_module

    def always_overflow(shape, font_family, block_index, prop):
        raise RenderError(block_index, prop, "text overflows frame: needs 999pt, frame provides 1pt")

    monkeypatch.setattr(pptx_module, "check_overflow", always_overflow)

    ds = load("reference@1.0.0", root=ds_root)
    planner = _AlwaysFailsPlanner(ds.spec)
    out = tmp_path / "out.pptx"

    try:
        plan_with_repair("brief", ds, "pptx", planner, out, max_attempts=3)
        assert False, "expected RenderError"
    except RenderError as e:
        assert "exhausted 3 repair attempts" in str(e)
    assert planner.calls == 3
