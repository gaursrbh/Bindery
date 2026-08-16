"""Shared schema flattening for Planner backends — M1-spec.md §2.2, extended
for the Claude CLI backend.

Both Ollama's `format:` field and Claude Code's `--json-schema` flag need a
single self-contained JSON Schema object, not M0's `allOf: [{$ref:
"core.schema.json"}, {...}]` envelope — neither compiler resolves the
external filename ref (only local `#/$defs/...` refs work, M1-spec.md §2.2).

Bug fixed here, found while building the Claude CLI backend: the original
merge did `{**core["properties"], **target_branch["properties"]}` — a
*shallow* merge. Since both core and the target vocab define a "blocks" key
(core: `type: array, minItems, maxItems, items`; target: `items` only, to
narrow the item shape), the shallow merge let target's `{"items": ...}`
completely replace core's dict, silently dropping `type: "array"` and the
min/max constraints. Ollama's grammar compiler tolerated the missing
`type: "array"` silently; Claude Code's stricter `--json-schema` validator
rejected it and the model degraded to stringifying `blocks` instead of
returning a real array (caught via a real CLI call, not a lint). Fixed by
merging shared keys one level deep instead of replacing them outright.
"""

from __future__ import annotations

import json

from bindery.ds.loader import SCHEMA_ROOT


def flatten_effective_schema(effective_schema: dict) -> dict:
    with open(SCHEMA_ROOT / "core.schema.json") as f:
        core = json.load(f)

    core_branch, target_branch = effective_schema["allOf"]
    assert "$ref" in core_branch  # sanity: M0-spec.md §2's fixed allOf[0] shape

    merged_props = dict(core["properties"])
    for key, value in target_branch.get("properties", {}).items():
        existing = merged_props.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged_props[key] = {**existing, **value}
        else:
            merged_props[key] = value

    return {
        "type": "object",
        "additionalProperties": False,
        "required": core["required"],
        "properties": merged_props,
        "$defs": effective_schema.get("$defs", {}),
    }
