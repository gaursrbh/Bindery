"""Token compliance linter dispatch — mainPRD R6, M3-spec.md §2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bindery.ds.loader import DesignSystem
from bindery.lint import pptx as _pptx
from bindery.lint import web as _web


@dataclass
class LintViolation:
    location: str
    kind: str
    value: str


_LINTERS = {"pptx": _pptx.lint, "web": _web.lint}


def allowed_values(ds: DesignSystem) -> set[str]:
    values: set[str] = set()
    for category in ds.tokens.values():
        if not isinstance(category, dict):
            continue
        for entry in category.values():
            value = entry.get("value") if isinstance(entry, dict) else entry
            if value is not None:
                values.add(str(value))
    return values


def lint(artifact_path: Path, ds: DesignSystem, target: str) -> list[LintViolation]:
    linter = _LINTERS.get(target)
    if linter is None:
        raise ValueError(f"no linter for target {target!r}")
    return linter(artifact_path, ds)
