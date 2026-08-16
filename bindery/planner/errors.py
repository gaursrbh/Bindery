"""M1-spec.md §2.2: Planner-internal failures only — a schema-invalid-but-
valid-JSON response is NOT a PlannerError, it's a CompositionError from the
subsequent render() call."""

from __future__ import annotations


class PlannerError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message
