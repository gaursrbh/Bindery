"""Shared prompt construction — used by every Planner backend."""

from __future__ import annotations

import json

from bindery.ds.loader import DesignSystem
from bindery.planner.base import RepairContext
from bindery.planner.components import describe_components


def build_system_prompt(ds: DesignSystem, target: str) -> str:
    components = describe_components(ds, target)
    lines = [
        "You are the Planner in a slide-generation pipeline. Given a brief, "
        "produce a single Composition IR JSON object.",
        f'Set "schema" to "bindery/v1", "design_system" to "{ds.spec}", '
        f'"target" to "{target}".',
        "Use ONLY these components:",
    ]
    for c in components:
        lines.append(f"- {c.name}: {c.description}")
    lines.append(
        "Never invent props, colors, coordinates, or font sizes not present "
        "in the schema. Output ONLY the JSON object, nothing else."
    )
    return "\n".join(lines)


def build_user_prompt(brief: str, repair: RepairContext | None) -> str:
    if repair is None:
        return f"Brief:\n{brief}\n\nProduce the Composition IR JSON now."
    return (
        f"Brief:\n{brief}\n\n"
        f"Your previous Composition IR failed to render:\n{repair.error}\n\n"
        f"Previous output:\n{json.dumps(repair.prior_composition)}\n\n"
        "Revise ONLY the text in the offending block/prop named above so it "
        "fits the available space (state a numeric target size to yourself and "
        "shorten to fit it). Keep every other block and prop byte-identical. "
        "Output ONLY the corrected Composition IR JSON object."
    )
