# Bindery M0 — Build-Ready Spec

Resolves the three blocking §12 open questions (issues #2, #3, #4) into a concrete
spec for M0: **IR schema, DS loader, PPTX renderer, CLI, no models** — a
hand-authored composition renders to a correct, on-brand deck (mainPRD §10,
Milestones table).

M0 does not touch the Planner, so decisions #1 (structured-output enforcement) and
#2 (planner size) don't drive any M0 code — they're recorded here so M1 starts from
a settled answer instead of re-litigating. Decision #3 (IR generalization) is the
one M0 actually builds on.

## 1. Decisions carried forward

| # | Question | Answer | Source |
|---|---|---|---|
| 1 | Structured-output enforcement | Ollama JSON-schema-enforced sampling (`format: <schema>`) is the only mechanism tested that gives a *structural*, not statistical, guarantee. Claude forced tool-use is a viable fallback (5/6) but not a hard guarantee. Applies at M1, not M0 — M0 has no Planner. | issue #2, `spike/RESULTS.md` |
| 2 | Minimum viable Planner size | 7B (`qwen2.5:7b-instruct-q4_K_M` class) matches 14B on schema validity (20/20 both) and structural sensibility (13/20 both) at 2.35x lower latency. Applies at M1. | issue #3, `spike/RESULTS-planner-size.md` |
| 3 | IR generalization across targets | Shared 4-field core envelope (`schema`, `design_system`, `target`, `blocks`) + per-target vocab schema that owns **every** component definition, including ones that exist in more than one target (no shared `$defs` across target files). This is what M0's schema layout below implements. | issue #4, `spike/RESULTS-ir-generalization.md` |

## 2. IR schema

### 2.1 File layout

```
schema/
├── core.schema.json     # target-agnostic envelope — do not add components here
├── pptx.schema.json     # pptx vocab: title, stat-trio, bullet-list, image-callout
└── web.schema.json      # present for shape parity; unused until M2, not built in M0
```

`schema/core.schema.json` and `schema/pptx.schema.json` are promoted from
`spike/core.schema.json` / `spike/pptx.schema.json` unchanged — the spike already
validated and rendered against them. `bindery.pptx/v1` from issue #2's spike
(`spike/schema.json`) is superseded by this core+vocab split per the issue #4
recommendation; nothing in an already-validated composition's `blocks` changes.

### 2.2 Core envelope (`schema/core.schema.json`)

Four fields, nothing about components:

```json
{
  "schema": "bindery/v1",
  "design_system": "acme@2.1.0",
  "target": "pptx",
  "blocks": [ { "component": "...", "props": { } } ]
}
```

- `design_system` pattern: `^[a-z0-9_-]+@[0-9]+\.[0-9]+\.[0-9]+$` — enforces exact
  resolved version at validation time (mainPRD §6.1: "resolved to exact version at
  bind time"). The DS loader (§3) is what performs `acme@2.x` → `acme@2.1.0`
  resolution *before* a composition is validated; the schema itself never sees a
  version range.
- `blocks`: 1–12 items (mainPRD R4 slide-count sanity bound; revisit if a DS needs
  more).
- `target`: `pptx | web | infographic`, per mainPRD §6.1. M0 only ships the `pptx`
  vocab; `web` and `infographic` are valid enum values with no vocab schema yet —
  validating a `web`/`infographic` composition in M0 is out of scope and expected
  to fail at the DS-loader step (§3.3), not the schema step.

### 2.3 PPTX vocab (`schema/pptx.schema.json`)

`allOf`-refs `core.schema.json`, narrows `target` to `const: "pptx"`, narrows
`blocks.items` to a `oneOf` of four components, each `additionalProperties: false`
at both the block level and the `props` level:

| Component | Required props | Optional props |
|---|---|---|
| `title` | `headline` (≤90 chars) | `eyebrow` (≤40), `accent` (`primary`\|`secondary`\|`neutral`) |
| `stat-trio` | `stats`: exactly 3 × `{value ≤12, label ≤30, delta? ≤10}` | — |
| `bullet-list` | `items`: 2–6 × string (≤120 each) | `heading` (≤60) |
| `image-callout` | `asset` (≤100), `caption` (≤100) | `accent` |

Copy verbatim from `spike/pptx.schema.json` — it's already been rendered end to
end (`spike/render_pptx.py` → `spike/out-pptx.pptx`, opened and text-frame-verified).

### 2.4 DS schema overrides (`schema/overrides.json` per mainPRD §6.2)

This was the one item flagged "currently just a stub in the PRD" (issue #1 notes).
Given issue #4's finding — a target vocab schema owns its components outright,
`additionalProperties: false` all the way down — a DS cannot silently loosen the
shared vocab. `overrides.json` is therefore **additive-only**: a DS may declare
extra components or extra optional props on top of the base target vocab, never
remove a required prop or widen an enum already present in the base schema.

`design-systems/<name>/schema/overrides.json`:

```json
{
  "pptx": {
    "components": {
      "quote-block": {
        "props": {
          "type": "object",
          "additionalProperties": false,
          "required": ["quote", "attribution"],
          "properties": {
            "quote": { "type": "string", "maxLength": 200 },
            "attribution": { "type": "string", "maxLength": 60 }
          }
        }
      }
    },
    "extend_props": {
      "title": {
        "optional": {
          "kicker_icon": { "enum": ["arrow", "flag", "star"] }
        }
      }
    }
  }
}
```

The DS loader (§3.2) merges this into an **effective schema**
(`base target vocab ∪ overrides.components` as extra `oneOf` branches,
`extend_props` merged into the matching component's `properties`/`optional`) at DS
load time, in memory — the merged result is never written back to
`schema/pptx.schema.json`. `additionalProperties: false` is preserved on every
merged object. If a DS has no `schema/overrides.json`, the effective schema is the
base vocab unchanged. Validation error messages (R3: "fails with a message listing
available components") are generated against the *effective* schema, so a DS's
custom component shows up in the "available components" list.

M0 ships zero reference DSes with a non-trivial `overrides.json` — the merge code
must exist and be tested (empty override, additive component, additive optional
prop), but no M0 acceptance criterion depends on a DS actually using it.

## 3. Design System loader

Implements mainPRD R2. Package: `bindery/ds/loader.py`.

### 3.1 Directory contract

A design system is a directory matching mainPRD §6.2:

```
design-systems/<name>/
├── system.yaml
├── tokens.json
├── components/pptx/*.py        # one layout fn module per component
└── schema/overrides.json       # optional
```

`system.yaml` required fields: `name`, `version` (semver), `description`,
`targets` (list, must include `pptx` for M0's one reference DS). Loader rejects
any DS missing `pptx.py` layout modules for a component the effective schema
declares, at load time — not at render time — so a broken DS fails fast (R2).

### 3.2 Loader interface

```python
class DesignSystem:
    name: str
    version: str                    # exact, resolved
    tokens: dict                    # parsed tokens.json
    effective_schema: dict          # base vocab + overrides.json, merged
    layout_fns: dict[str, Callable] # component name -> pptx layout function
    path: Path

def load(name_or_spec: str, root: Path = Path("design-systems")) -> DesignSystem:
    """
    name_or_spec: "acme" (any installed version, must be exactly one) or
    "acme@2.1.0" (exact) or "acme@2.x" (resolves to highest installed 2.y.z).
    Raises DesignSystemError with the offending file + field on any
    malformed system.yaml, missing tokens.json, or unresolvable version range.
    """

def list_installed(root: Path = Path("design-systems")) -> list[DesignSystem]: ...

def validate(ds: DesignSystem) -> list[ValidationIssue]:
    """Structural check only: system.yaml schema, tokens.json parses, every
    component in effective_schema has a matching layout_fns entry. Does not
    touch any composition."""
```

`DesignSystemError` message format (R2 acceptance criterion): `"<file>: <field>:
<what's wrong>"`, e.g. `system.yaml: version: "2.x" is not valid semver`.

### 3.3 Version resolution

- `acme` (bare) → error if more than one version installed, resolve if exactly one.
- `acme@2.1.0` (exact) → error if not installed.
- `acme@2.x` / `acme@2` → highest installed version matching the prefix. Resolution
  happens once, at `load()`, and the exact resolved string (`acme@2.1.0`) is what
  gets written into `bindery.lock` (mainPRD §6.6) and is the only form the IR
  schema's `design_system` field ever contains — ranges never reach validation.

## 4. PPTX renderer

Implements mainPRD R4, §6.4 (`(Composition, DesignSystem) → Artifact`, pure,
deterministic). Package: `bindery/render/pptx.py`.

### 4.1 Interface

```python
def render(composition: dict, ds: DesignSystem, out_path: Path) -> RenderResult:
    """
    1. Validate composition against ds.effective_schema (jsonschema). On failure,
       raise CompositionError listing available components (R3) — this is the
       last validation gate before pixels; the CLI's repair-loop hook (M1) wraps
       this call, M0 has none.
    2. For each block, look up ds.layout_fns[block["component"]] and call it with
       (props, ds.tokens, slide) — one function per component, pattern lifted
       from spike/render_pptx.py.
    3. Save .pptx to out_path.
    4. Measure text-frame overflow per placed run (python-pptx does not
       auto-detect this — M0 renderer must compute it: text width at the DS's
       token font size/family vs. frame width, using PIL's ImageFont.getlength
       or equivalent, no rendering round-trip). Overflow raises
       RenderError naming the block index + prop, not a silent clip — R4 requires
       "every text frame fits without overflow" as an acceptance criterion, so
       this cannot be a warning.
    """

@dataclass
class RenderResult:
    path: Path
    duration_ms: int
    blocks_rendered: int
```

### 4.2 Component → layout function contract

One Python module per component under `design-systems/<name>/components/pptx/`,
same shape the PRD tree shows (`title.py`, `stat-trio.py`). Each module exports:

```python
def layout(slide, props: dict, tokens: dict) -> None:
    """Places shapes on `slide` (an existing python-pptx Slide, blank layout).
    Reads only `props` and `tokens` — no filesystem, no network, no randomness,
    no wall-clock. Pure per §6.4."""
```

M0 ships four modules for the one reference DS (`title.py`, `stat-trio.py`,
`bullet-list.py`, `image-callout.py`), ports of `spike/render_pptx.py`'s inline
logic split one-function-per-file instead of one script.

### 4.3 What M0 explicitly does not build

- Preview rasterization (LibreOffice headless) — M3.
- Token compliance linting (R6) — M3; M0's renderer must still *only* pull colors/
  fonts/spacing from `ds.tokens`, never hardcode a hex value, so the M3 linter has
  something to check against, but M0 ships no linter itself.
- The repair loop (mainPRD §7 step 3) — needs a Planner, M1.

## 5. CLI

Implements mainPRD R10. Package: `bindery/cli.py`, entry point `bindery`.

### 5.1 M0 command surface

```
bindery generate <composition.json> --ds <name@version> --out <dir> [--ds-root <path>]
```

- `<composition.json>`: hand-authored IR (M0 has no Planner — this is the file a
  human writes directly per the milestone's own description).
- `--ds`: passed straight to `loader.load()` (§3.2) — accepts exact or range form.
- `--out`: output directory; renderer writes `<out>/<composition-stem>.pptx`.
- `--ds-root`: defaults to `./design-systems`, override for testing against a
  non-default tree.

### 5.2 Behavior

1. Load composition JSON from disk.
2. `ds = loader.load(args.ds, root=args.ds_root)` — on `DesignSystemError`, print
   the message from §3.2 to stderr, exit 2.
3. `render.render(composition, ds, out_path)` — on `CompositionError`, print the
   validation failure (available components list included, R3) to stderr, exit 3.
   On `RenderError` (overflow etc.), print block index + prop to stderr, exit 4.
4. On success, print the written path to stdout, exit 0.

No `bindery.lock` writing in M0 (R8/§6.6 needs `models` — meaningless with no
Planner — and is scoped to M3's "lockfile round-trip" exit criterion); M0's CLI
output is just the rendered file. Re-render-from-lock (R8) and GUI parity are both
out of scope here — M0's exit criterion (§10) only requires the hand-authored path
to work.

## 6. File/task breakdown for M0

```
schema/
  core.schema.json                    # from spike/core.schema.json, unchanged
  pptx.schema.json                    # from spike/pptx.schema.json, unchanged
  web.schema.json                     # from spike/web.schema.json, unused until M2

bindery/
  ds/
    loader.py                         # §3.2–3.3
    errors.py                         # DesignSystemError
  render/
    pptx.py                           # §4.1, §4.3
    overflow.py                       # text-frame fit measurement, §4.1 step 4
    errors.py                         # CompositionError, RenderError
  cli.py                              # §5

design-systems/
  reference/                          # one reference DS per M0 exit criterion
    system.yaml
    tokens.json
    components/pptx/
      title.py
      stat-trio.py
      bullet-list.py
      image-callout.py
    # no schema/overrides.json — exercises the "no override" path

tests/
  test_loader.py                      # malformed system.yaml, version resolution
  test_overrides_merge.py             # empty / additive-component / additive-prop
  test_render_pptx.py                 # one composition per component, overflow case
  test_cli.py                         # success + each of the three error exits
```

## 7. Reproducing / starting point

The spike code already does most of §2 and half of §4 for one throwaway DS
(`spike/tokens.json`, `spike/render_pptx.py`). Porting it into `bindery/` and
`design-systems/reference/` per §6, plus writing `bindery/ds/loader.py` (net new —
the spike never built a loader, it read `tokens.json` directly) is the M0 build
order: loader first (nothing else has a `DesignSystem` object to render against),
then the overrides merge, then the CLI wiring, then the four layout-fn ports.
