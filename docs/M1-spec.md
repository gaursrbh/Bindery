# Bindery M1 — Build-Ready Spec

Resolves the four decision tickets on the [Bindery M1 build-ready spec map](https://github.com/gaursrbh/Bindery/issues/12)
(issues #13–#16) into a concrete spec for M1: **Planner integration, structured-output
enforcement, validation repair loop** — a natural-language brief produces a usable
deck without hand-editing the IR (mainPRD §10, Milestones table).

M1 builds on M0 (merged to `main`, PR #10) — IR schema, DS loader, PPTX renderer,
CLI all exist and are unchanged by this spec except where noted (new CLI
subcommand, one new `DesignSystem` field).

## 1. Decisions carried forward

| # | Question | Answer | Source |
|---|---|---|---|
| 1 | Repair-loop scope | Real failures are render-time **overflow**, not schema validation — schema-constrained decoding is saturated (20/20 first-attempt valid, confirmed twice). The loop wraps `render()`, catching `RenderError` (and `CompositionError`, rare). | issue #13 |
| 2 | Repair prompt format | Prior error + full prior IR + "fix only the named block/prop"; must state a numeric pt target, not "shorten it"; one retry is not always sufficient, keep the 3-attempt cap. | issue #13 |
| 3 | `overrides.json` → Planner | Merge mechanism already built in M0 (`_merge_overrides`, tested). New: optional `description` field per component/extended prop; `DesignSystem.component_docs` field; base-four descriptions live in `bindery/planner/`; `describe_components(ds, target)` merges both. No component-count scoping in M1. | issue #14 |
| 4 | Planner interface | `typing.Protocol`, one method `plan(brief, ds, target, *, repair=None) -> dict`; one implementation `OllamaPlanner`; `PlannerConfig` dataclass; stdlib `urllib`; `PlannerError` for infra failures; stateless — retry loop lives outside the Planner. | issue #15 |
| 5 | CLI shape | New `bindery plan` subcommand (not a polymorphic `generate`); brief = mainPRD §6.1 YAML minus `sources`; `--ds`/`--target` optional overrides; new exit code 5 for `PlannerError`; repair-exhausted failures reuse the underlying code with an attempt-count message; `--model` flag only; one stderr line per repair attempt. | issue #16 |

## 2. Planner

Package: `bindery/planner/`.

### 2.1 Interface (`bindery/planner/base.py`)

```python
class RepairContext:
    prior_composition: dict
    error: str
    attempt: int

class Planner(Protocol):
    def plan(
        self, brief: str, ds: DesignSystem, target: str, *, repair: RepairContext | None = None
    ) -> dict:
        """Returns a raw, unvalidated Composition dict. Derives its prompt
        (component descriptions, effective schema for Ollama's `format:` field)
        internally from `ds` — callers pass nothing else. Stateless: does not
        loop or retry itself."""
```

### 2.2 `OllamaPlanner` (`bindery/planner/ollama.py`)

```python
@dataclass
class PlannerConfig:
    model: str = "qwen2.5:7b-instruct-q4_K_M"   # issue #3
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    seed: int = 42

class OllamaPlanner:
    def __init__(self, config: PlannerConfig = PlannerConfig()): ...
    def plan(self, brief, ds, target, *, repair=None) -> dict:
        """POST {base_url}/api/generate via stdlib urllib (no new dependency),
        format=ds.effective_schemas[target] (schema-constrained decoding,
        issue #2's structural guarantee). System prompt built from
        describe_components(ds, target) (§2.3). If `repair` is set, the user
        prompt appends: the RenderError/CompositionError message, the full
        prior composition JSON, and 'fix only the named block/prop; state a
        numeric pt target when shortening text' (issue #13's tested shape).
        Raises PlannerError on network failure, non-2xx response, or a
        response body that isn't valid JSON at all — NOT on schema-invalid-
        but-valid-JSON, which is a render()-time CompositionError instead."""
```

`bindery/planner/errors.py::PlannerError` — same per-package error pattern as
`DesignSystemError`/`CompositionError`/`RenderError`.

### 2.3 Component discovery (`bindery/planner/components.py`)

```python
_BASE_COMPONENT_DOCS: dict[str, str] = {
    "title": "...",
    "stat-trio": "...",
    "bullet-list": "...",
    "image-callout": "...",
}  # authored once for M1; not derived from ds

def describe_components(ds: DesignSystem, target: str) -> list[ComponentDoc]:
    """Merges _BASE_COMPONENT_DOCS with ds.component_docs[target] (DS-added,
    from overrides.json) into what the system prompt enumerates. All
    components always shown — no count-based scoping in M1 (issue #14)."""
```

**DS loader change** (`bindery/ds/loader.py`): `DesignSystem` gains
`component_docs: dict[str, dict[str, str]] = field(default_factory=dict)`,
populated by `_load_effective_schemas` (or a sibling function) from
`overrides.json`'s new optional `description` field on `components` entries and
`extend_props.*.optional.*` entries. Loader stays DS-agnostic — it never knows
about the base four.

`schema/overrides.json` shape gains one optional field (additive, M0's shipped
overrides files stay valid):

```json
{
  "pptx": {
    "components": {
      "quote-block": {
        "description": "A pull-quote with attribution; use for a single strong verbatim statement, not a paraphrase.",
        "props": { "...": "..." }
      }
    },
    "extend_props": {
      "title": {
        "optional": {
          "kicker_icon": {
            "description": "Small icon next to the eyebrow text.",
            "enum": ["arrow", "flag", "star"]
          }
        }
      }
    }
  }
}
```

## 3. Repair loop

Not a Planner method — a small orchestration function, `bindery/planner/repair.py`:

```python
def plan_with_repair(
    brief: str, ds: DesignSystem, target: str, planner: Planner, out_path: Path,
    max_attempts: int = 3,
) -> RenderResult:
    """attempt 1: composition = planner.plan(brief, ds, target)
    then render(composition, ds, out_path).
    On CompositionError/RenderError: build RepairContext(prior_composition,
    str(error), attempt), call planner.plan(..., repair=ctx), render again.
    Print one line per attempt to stderr (issue #16). After max_attempts,
    re-raise the last error with a message naming the attempt count —
    same error type/exit code as a first-attempt failure, per issue #16."""
```

## 4. CLI

Implements mainPRD R10 (extended). Package: `bindery/cli.py`.

### 4.1 New command surface

```
bindery plan <brief.yaml> --ds <name@version> [--target pptx] [--model <name>] --out <dir> [--ds-root <path>]
```

- `<brief.yaml>`: mainPRD §6.1 shape minus `sources` — `intent`, `target`,
  `design_system`, `constraints` (`max_slides`, `audience`, `tone`,
  `must_include`).
- `--ds`, `--target`: optional; override the brief's inline `design_system`/
  `target` fields if given, otherwise the brief's fields are used; error if
  neither present.
- `--model`: optional; overrides `PlannerConfig.model`. No `--base-url`/
  `--temperature`/`--seed` flags in M1 (no stated need yet).
- `--out`, `--ds-root`: same as `generate` (M0, unchanged).

`bindery generate` (M0) is unchanged — composition JSON in, no model, no
network. `plan` is additive, not a replacement.

### 4.2 Behavior and exit codes

Extends M0-spec.md §5.2's table:

| Code | Meaning | Where |
|---|---|---|
| 0 | success | — |
| 2 | `DesignSystemError` | unchanged from M0 |
| 3 | `CompositionError` (incl. repair-exhausted) | `render()`; message names attempt count if repair-exhausted |
| 4 | `RenderError` (incl. repair-exhausted) | `render()`; message names attempt count if repair-exhausted |
| 5 | `PlannerError` | new — Ollama unreachable, model not pulled, non-JSON response |

Progress: one line per repair attempt to stderr (`"attempt 2/3: retrying after
overflow in block 0 (title)"` or equivalent) — `plan()` calls run ~10-25s
(issues #3/#13) and can fire up to 3×; silence that long reads as a hang.

No `bindery.lock` writing in M1 either (still scoped to M3's "lockfile
round-trip" exit criterion) — `PlannerConfig`'s fields (model, seed) are exactly
what the lock will eventually record (mainPRD §6.6), but M1 doesn't write it.

## 5. File/task breakdown for M1

```
bindery/
  planner/
    base.py          # Planner protocol, RepairContext — §2.1
    ollama.py         # OllamaPlanner, PlannerConfig — §2.2
    components.py      # _BASE_COMPONENT_DOCS, describe_components() — §2.3
    repair.py         # plan_with_repair() orchestration — §3
    errors.py         # PlannerError
  ds/
    loader.py          # +DesignSystem.component_docs, overrides.json description parsing — §2.3
  cli.py               # +`plan` subcommand — §4

schema/
  overrides.json (per-DS, optional)  # +description field, additive — §2.3

tests/
  test_planner_prompt.py    # describe_components() merges base + DS-added docs
  test_planner_ollama.py    # PlannerError on unreachable/non-JSON; plan() shape (mock Ollama HTTP)
  test_repair_loop.py       # convergence + max_attempts exhaustion (real or recorded Ollama responses)
  test_cli_plan.py          # brief parsing, --ds/--target override precedence, exit code 5, repair-exhausted messages
```

## 6. Reproducing / starting point

Real failure material for `test_repair_loop.py` should follow the method used
to resolve issue #13: run the real Planner (`qwen2.5:7b-instruct-q4_K_M`) against
`spike/briefs.json`, and to force genuine overflow (M0's reference DS textboxes
are generous enough that organic overflow didn't occur — 0/20 in testing) render
against a design system with deliberately tighter box geometry, not synthetic/
hand-written error injection. Schema-validation failures should not be
manufactured as repair-loop test fixtures — they don't occur under schema-
constrained decoding and testing against them tests a path M1 won't exercise
in practice.

Build order: `bindery/planner/errors.py` and `base.py` first (nothing else has
a `Planner` type to reference), then `ollama.py` + `components.py` (parallel —
independent of each other), then the `DesignSystem.component_docs` loader
change, then `repair.py` (depends on all of the above), then the CLI `plan`
subcommand (depends on `repair.py`).
