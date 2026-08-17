import json

from bindery.ds import loader


def test_no_overrides_file_leaves_schema_unchanged(ds_root):
    ds = loader.load("reference", root=ds_root)
    base_defs = set(ds.effective_schemas["pptx"]["$defs"])
    assert base_defs == {
        "title", "statTrio", "bulletList", "imageCallout",
        "featureGrid", "statGroup", "signalTable",
    }


def test_additive_component(ds_root):
    schema_dir = ds_root / "reference" / "schema"
    schema_dir.mkdir()
    (schema_dir / "overrides.json").write_text(
        json.dumps(
            {
                "pptx": {
                    "components": {
                        "quote-block": {
                            "props": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["quote", "attribution"],
                                "properties": {
                                    "quote": {"type": "string", "maxLength": 200},
                                    "attribution": {"type": "string", "maxLength": 60},
                                },
                            }
                        }
                    }
                }
            }
        )
    )
    (ds_root / "reference" / "components" / "pptx" / "quote-block.py").write_text(
        "def layout(slide, props, tokens):\n    pass\n"
    )

    ds = loader.load("reference", root=ds_root)
    assert "quote-block" in ds.layout_fns["pptx"]
    schema = ds.effective_schemas["pptx"]
    assert "quote_block_override" in schema["$defs"]
    oneof = schema["allOf"][1]["properties"]["blocks"]["items"]["oneOf"]
    assert {"$ref": "#/$defs/quote_block_override"} in oneof


def test_additive_optional_prop_on_existing_component(ds_root):
    schema_dir = ds_root / "reference" / "schema"
    schema_dir.mkdir()
    (schema_dir / "overrides.json").write_text(
        json.dumps(
            {
                "pptx": {
                    "extend_props": {
                        "title": {
                            "optional": {
                                "kicker_icon": {"enum": ["arrow", "flag", "star"]}
                            }
                        }
                    }
                }
            }
        )
    )

    ds = loader.load("reference", root=ds_root)
    title_props = ds.effective_schemas["pptx"]["$defs"]["title"]["properties"]["props"]
    assert "kicker_icon" in title_props["properties"]
    # required props untouched
    assert title_props["required"] == ["headline"]
