"""Repair-loop orchestration — M1-spec.md §3.

Not a Planner method: Planner.plan() is stateless, this owns the max-attempt
loop across plan() -> render() -> (on failure) plan(repair=...) -> render().
"""

from __future__ import annotations

import sys
from pathlib import Path

from bindery.ds.loader import DesignSystem
from bindery.planner.base import Planner, RepairContext
from bindery.render.errors import CompositionError, RenderError
from bindery.render.pptx import RenderResult, render


def plan_with_repair(
    brief: str,
    ds: DesignSystem,
    target: str,
    planner: Planner,
    out_path: Path,
    max_attempts: int = 3,
) -> RenderResult:
    composition: dict | None = None
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        repair = None
        if last_error is not None:
            print(
                f"attempt {attempt}/{max_attempts}: retrying after {last_error}",
                file=sys.stderr,
            )
            repair = RepairContext(
                prior_composition=composition, error=str(last_error), attempt=attempt - 1
            )

        composition = planner.plan(brief, ds, target, repair=repair)

        try:
            return render(composition, ds, out_path)
        except (CompositionError, RenderError) as e:
            last_error = e

    assert last_error is not None
    last_error.args = (
        f"{last_error.args[0] if last_error.args else last_error} "
        f"(exhausted {max_attempts} repair attempts)",
    )
    raise last_error
