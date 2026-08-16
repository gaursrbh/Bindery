"""(Composition, DesignSystem) -> single-file HTML slide deck.

An alternative to the pptx target: same 4-component vocab, but layout is
delegated entirely to CSS flexbox instead of manually-computed absolute
coordinates. This makes the whole class of bug fixed in issue #36 (blocks
placed at hardcoded/overlapping coordinates) structurally impossible here —
the browser's box model stacks blocks in document order, there is no y-cursor
to get wrong. Pure Python string templating, no Node/Vite pipeline (unlike
the "web" target) — the component contract is the simplest of any target:
`layout(props, tokens) -> str`, an HTML fragment, no position/size math.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from bindery.ds.loader import SCHEMA_ROOT, DesignSystem
from bindery.render.errors import CompositionError

_CORE_SCHEMA = json.loads((SCHEMA_ROOT / "core.schema.json").read_text())
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


def _tokens_css(tokens: dict) -> str:
    lines = [":root {"]
    for category, entries in tokens.items():
        if not isinstance(entries, dict):
            continue
        for name, spec in entries.items():
            value = spec.get("value") if isinstance(spec, dict) else spec
            if value is None:
                continue
            if category == "typography" and name.endswith("size") and str(value).isdigit():
                value = f"{value}px"
            lines.append(f"  --{category}-{name}: {value};")
    lines.append("}")
    return "\n".join(lines)


_PAGE_CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #ddd; font-family: var(--typography-family, sans-serif); }
.deck { display: flex; flex-direction: column; align-items: center; gap: 24px; padding: 24px; }
.slide {
  width: 960px; height: 540px; background: var(--color-background, #fff);
  box-shadow: 0 2px 12px rgba(0,0,0,0.15); padding: 48px;
  display: flex; flex-direction: column; gap: 20px; overflow: hidden;
}
@media print {
  html, body { background: #fff; }
  .deck { padding: 0; gap: 0; }
  .slide { box-shadow: none; page-break-after: always; }
}
"""


def render(composition: dict, ds: DesignSystem, out_path: Path) -> RenderResult:
    start = time.monotonic()
    _validate(composition, ds)

    layout_fns = ds.layout_fns["html-slides"]
    tokens = ds.tokens

    slides: list[list[str]] = []
    for block in composition["blocks"]:
        component = block["component"]
        fragment = layout_fns[component](block["props"], tokens)
        if component == "title" or not slides:
            slides.append([fragment])
        else:
            slides[-1].append(fragment)

    slides_html = "\n".join(
        f'<section class="slide">{"".join(fragments)}</section>' for fragments in slides
    )
    html = (
        "<!doctype html>\n<html><head><meta charset=\"utf-8\">"
        f"<style>{_tokens_css(tokens)}\n{_PAGE_CSS}</style></head>"
        f'<body><div class="deck">{slides_html}</div></body></html>\n'
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)

    return RenderResult(
        path=out_path,
        duration_ms=int((time.monotonic() - start) * 1000),
        blocks_rendered=len(composition["blocks"]),
    )
