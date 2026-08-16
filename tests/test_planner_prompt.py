import json

from bindery.ds.loader import load
from bindery.planner.components import describe_components
from bindery.planner.ollama import _build_system_prompt


def test_describe_components_base_only(ds_root):
    ds = load("reference@1.0.0", root=ds_root)
    docs = describe_components(ds, "pptx")
    names = {d.name for d in docs}
    assert names == {"title", "stat-trio", "bullet-list", "image-callout"}
    for d in docs:
        assert d.description and d.description != d.name


def test_describe_components_merges_ds_added(ds_root):
    overrides_dir = ds_root / "reference" / "schema"
    overrides_dir.mkdir(exist_ok=True)
    (overrides_dir / "overrides.json").write_text(
        json.dumps(
            {
                "pptx": {
                    "components": {
                        "quote-block": {
                            "description": "A pull-quote with attribution.",
                            "props": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["quote", "attribution"],
                                "properties": {
                                    "quote": {"type": "string", "maxLength": 200},
                                    "attribution": {"type": "string", "maxLength": 60},
                                },
                            },
                        }
                    }
                }
            }
        )
    )
    (ds_root / "reference" / "components" / "pptx" / "quote-block.py").write_text(
        "def layout(slide, props, tokens):\n    pass\n"
    )
    ds = load("reference@1.0.0", root=ds_root)
    docs = describe_components(ds, "pptx")
    quote_doc = next(d for d in docs if d.name == "quote-block")
    assert quote_doc.description == "A pull-quote with attribution."


def test_system_prompt_lists_components(ds_root):
    ds = load("reference@1.0.0", root=ds_root)
    prompt = _build_system_prompt(ds, "pptx")
    assert "reference@1.0.0" in prompt
    assert "stat-trio" in prompt
    assert "bindery/v1" in prompt
