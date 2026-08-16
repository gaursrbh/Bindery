from pathlib import Path

from bindery.ds.loader import load
from bindery.planner.schema_utils import flatten_effective_schema


def test_blocks_keeps_type_array_after_merge(ds_root):
    """Regression test: the flatten used to shallow-merge core.properties
    and target.properties, so target's blocks.items silently replaced
    core's blocks (dropping type/minItems/maxItems) instead of merging."""
    ds = load("reference@1.0.0", root=ds_root)
    flat = flatten_effective_schema(ds.effective_schemas["pptx"])

    blocks = flat["properties"]["blocks"]
    assert blocks["type"] == "array"
    assert blocks["minItems"] == 1
    assert "items" in blocks
    assert "oneOf" in blocks["items"]
