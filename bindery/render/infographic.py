"""(Composition, DesignSystem) -> .svg (+ .png preview) — mainPRD R11,
M4-spec.md §2.

Component contract is `layout(props, tokens, x, y, width) -> (svg_fragment,
height_consumed)` — a correction made during implementation to M4-spec.md's
originally-stated `-> str`: the renderer needs each block's consumed height
to stack the next one, the same reason M0's PPTX renderer works off known
frame geometry rather than SVG's free-form coordinate space.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import cairosvg
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from bindery.ds.loader import SCHEMA_ROOT, DesignSystem
from bindery.render.errors import CompositionError

_CANVAS_WIDTH = 800
_MARGIN = 32

_CORE_SCHEMA = __import__("json").loads((SCHEMA_ROOT / "core.schema.json").read_text())
_REGISTRY = Registry().with_resource(
    "core.schema.json", Resource.from_contents(_CORE_SCHEMA)
)


@dataclass
class RenderResult:
    path: Path
    duration_ms: int
    blocks_rendered: int


def _validate(composition: dict, ds: DesignSystem) -> dict:
    target = composition.get("target")
    schema = ds.effective_schemas.get(target)
    if schema is None:
        raise CompositionError(
            f"design system '{ds.spec}' has no schema for target {target!r}; "
            f"available targets: {sorted(ds.effective_schemas)}"
        )
    schema_for_validation = {k: v for k, v in schema.items() if k != "$id"}
    validator = Draft202012Validator(schema_for_validation, registry=_REGISTRY)
    errors = sorted(validator.iter_errors(composition), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        location = "/".join(str(p) for p in first.path) or "<root>"
        raise CompositionError(f"composition invalid at {location}: {first.message}")
    return schema


def render(composition: dict, ds: DesignSystem, out_path: Path) -> RenderResult:
    start = time.monotonic()
    _validate(composition, ds)

    layout_fns = ds.layout_fns["infographic"]
    tokens = ds.tokens
    background = tokens.get("color", {}).get("background", {}).get("value", "#FFFFFF")

    fragments = []
    cursor_y = _MARGIN
    content_width = _CANVAS_WIDTH - 2 * _MARGIN

    for block in composition["blocks"]:
        fn = layout_fns[block["component"]]
        fragment, consumed = fn(block["props"], tokens, _MARGIN, cursor_y, content_width)
        fragments.append(fragment)
        cursor_y += consumed

    total_height = cursor_y + _MARGIN
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_CANVAS_WIDTH}" '
        f'height="{total_height}" viewBox="0 0 {_CANVAS_WIDTH} {total_height}">'
        f'<rect width="{_CANVAS_WIDTH}" height="{total_height}" fill="{background}"/>'
        + "".join(fragments)
        + "</svg>"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg)

    png_path = out_path.with_suffix(".png")
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(png_path))

    duration_ms = int((time.monotonic() - start) * 1000)
    return RenderResult(
        path=out_path, duration_ms=duration_ms, blocks_rendered=len(composition["blocks"])
    )
