"""Planner protocol — M1-spec.md §2.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from bindery.ds.loader import DesignSystem


@dataclass
class RepairContext:
    prior_composition: dict
    error: str
    attempt: int


class Planner(Protocol):
    def plan(
        self,
        brief: str,
        ds: DesignSystem,
        target: str,
        *,
        repair: RepairContext | None = None,
    ) -> dict:
        """Returns a raw, unvalidated Composition dict. Derives its prompt
        (component descriptions, effective schema for schema-constrained
        decoding) internally from `ds` — callers pass nothing else.
        Stateless: does not loop or retry itself."""
        ...
