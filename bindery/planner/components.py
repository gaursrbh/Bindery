"""Component discovery for Planner prompts — M1-spec.md §2.3.

Merges base-component descriptions (authored here, not derived from any DS)
with DS-added descriptions (ds.component_docs, from schema/overrides.json)
into what the system prompt enumerates. All components always shown — no
component-count scoping in M1 (issue #14).
"""

from __future__ import annotations

from dataclasses import dataclass

from bindery.ds.loader import DesignSystem

_BASE_COMPONENT_DOCS: dict[str, str] = {
    "title": "Slide headline with an optional eyebrow/kicker line above it. "
    "Use for the opening slide or a section divider.",
    "stat-trio": "Three side-by-side numeric callouts (value, label, optional "
    "delta). Use when the brief has three or fewer genuinely numeric facts to "
    "foreground; do not use for qualitative content.",
    "bullet-list": "An optional heading plus a list of short text items. Use "
    "for enumerable, non-numeric points — drivers, action items, agenda.",
    "image-callout": "A named image asset plus a caption. Use when the brief "
    "references a chart, photo, or diagram that isn't in this pipeline's "
    "source content — the asset is referenced by name, not generated.",
    "feature-grid": "2-4 side-by-side (title, description) cards. Use for "
    "parallel qualitative features/capabilities being introduced together — "
    "not for numeric facts (use stat-trio/stat-group) or a single list of "
    "enumerable points (use bullet-list).",
    "stat-group": "2-6 side-by-side numeric callouts (value, label) under an "
    "optional section heading. Use when there are more or fewer than exactly "
    "three numeric facts to foreground, or when multiple stat clusters need "
    "distinct headings on one slide; use stat-trio instead for exactly three.",
    "signal-table": "A two-column table of (signal, action) row pairs under "
    "an optional heading. Use for a brief that maps triggers/conditions to "
    "the corresponding response — not for a simple enumerable list.",
}


@dataclass
class ComponentDoc:
    name: str
    description: str


def describe_components(ds: DesignSystem, target: str) -> list[ComponentDoc]:
    docs = dict(_BASE_COMPONENT_DOCS)
    docs.update(
        {
            name: desc
            for name, desc in ds.component_docs.get(target, {}).items()
            if "." not in name  # component-level only; "comp.prop" entries are prop docs
        }
    )

    names = _component_names(ds.effective_schemas.get(target, {}))
    return [ComponentDoc(name=n, description=docs.get(n, n)) for n in names]


def _component_names(effective_schema: dict) -> list[str]:
    defs = effective_schema.get("$defs", {})
    names = []
    for def_schema in defs.values():
        const = def_schema.get("properties", {}).get("component", {}).get("const")
        if const:
            names.append(const)
    return names
