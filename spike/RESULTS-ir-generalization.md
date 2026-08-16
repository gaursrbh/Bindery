# IR generalization across targets — results

Answers issue #4 / mainPRD §12.3. Files: `core.schema.json` (the target-agnostic
envelope), `pptx.schema.json` / `web.schema.json` (target vocab overlays, `allOf`-ref
the core), `composition-pptx.json` / `composition-web.json` (one brief, rendered to
both targets — the title + stat-trio example from §6.3), `render_pptx.py` /
`render_web.py` (real renderers, `python-pptx` and inlined-CSS HTML), `tokens.json`
(one shared design system), `validate.py` (schema check harness).

## What was tested

Took the §6.3 example (`title` + `stat-trio`, "Q3 board update") and wrote it once,
then split it into two composition files that are **byte-identical in `blocks`** —
the only difference is the top-level `target` field (`pptx` vs `web`). Each validates
against its own target schema, which is the shared `core.schema.json` envelope
(`schema`, `design_system`, `target`, `blocks`) narrowed via `allOf` to a per-target
`oneOf` of components. Both compositions were then actually rendered — a real
`.pptx` via `python-pptx` and a real single-file `.html` — by two independent
renderer modules that read the identical `props` shape and the same `tokens.json`.

This is stronger than a schema-only check: it proves the *props*, not just the
JSON Schema, survive unmodified from one renderer to the other, which is what "the
model writes the specification, the renderer draws the pixels" (§2) actually
depends on.

## Result

**The shared-core-plus-target-vocab bet holds for the two components tested
(`title`, `stat-trio`).** Both compositions are valid, both rendered correctly
(verified by reading the text frames back out of the `.pptx` and inspecting the
HTML), and neither renderer needed a prop the other didn't have for these two
components. `core.schema.json` is 27 lines and needed zero target-specific
branching to define the envelope — `schema`/`design_system`/`target`/`blocks` are
genuinely universal.

**But the vocab does not stay identical past the shared components, in two
concrete ways found while building this:**

1. **Target-only components are real, not an edge case.** `pptx.schema.json` has
   `bullet-list` and `image-callout` (slide-paradigm, static). `web.schema.json`
   has `nav-bar` (a links list — no PPTX equivalent; a deck has no navigation
   chrome). This is exactly what mainPRD §12.3 predicted ("target-specific
   component vocabularies") — it's not a failure of the bet, it's the second half
   of it, and it means a component's home is a single target's schema file, not
   the core.

2. **A shared component's props can still need a target-only optional field.**
   `web.schema.json`'s `stat-trio` adds an optional `href` per stat (click-through
   to a detail page — meaningful on the web, meaningless in a static deck).
   `pptx.schema.json`'s `stat-trio` does not have this field, and correctly
   rejects it (`additionalProperties: false`). So "same component name, same
   required props" is not the same guarantee as "byte-identical schema" — each
   target vocab file has to independently define+maintain the shared components'
   shape, and a steward adding an optional field to one target has to remember it
   doesn't propagate to the other. This spike hand-copied `title`/`stat-trio`
   into both vocab files rather than sharing a `$defs` block between them; at
   scale that duplication is the real cost of this approach, not schema conflict.

## What did *not* need to differ (contrary to a plausible worry going in)

- **No coordinate/layout leakage into the IR.** Neither renderer needed pixel,
  inch, or grid-position data from the composition — `render_pptx.py` hardcodes
  slide geometry, `render_web.py` uses CSS grid. The IR stayed pure intent in
  both directions, which is the thing §2's guarantee actually depends on.
- **Token references resolved identically.** Both renderers pulled `primary` /
  `secondary` / `neutral` accent values out of the same `tokens.json` with no
  target-conditional logic. `"accent": "primary"` means the same thing in both
  files.
- **`maxLength` constraints held for both targets in this one composition** — no
  text needed different length budgets for PPTX's fixed-frame overflow vs. web's
  reflow. This is a small-n result (one composition, short strings); it's a
  reasonable early flag that per-target `maxLength` tuning may eventually be
  needed (a headline that fits a fixed PPTX text frame may be conservative for a
  web layout that can wrap), not a claim that it's ruled out.

## Recommendation

Keep the shared-core-plus-target-vocab architecture per mainPRD §12.3, with two
refinements to how it's implemented, both low-cost now and expensive to retrofit
later:

- **Give each target vocab schema, not the core, ownership of every component
  definition** — including ones that happen to exist in more than one target.
  Don't try to hoist "shared" components into `core.schema.json`'s `$defs` in a
  way that couples targets; `stat-trio` diverging (the `href` case) shows the
  coupling would need to be undone almost immediately. The core schema should
  stay exactly what it was here: the four-field envelope and nothing about
  components.
- **If duplication of shared component defs across target files becomes a real
  maintenance problem** (more targets, more shared components), address it with
  a codegen or `$defs`-merge step at DS-build time, not by weakening
  `additionalProperties: false` on either side — the whole point of §2's
  guarantee is that a target can't accept a prop it doesn't know what to do
  with.

No redesign needed before M1. `bindery.pptx/v1` from the issue #2 spike
(`spike/schema.json`) can be reframed as `core.schema.json` + `pptx.schema.json`
per this structure without changing any already-validated composition's `blocks`.

## Reproducing

```
cd spike
.venv/bin/pip install jsonschema python-pptx   # already set up from issue #2's spike
.venv/bin/python validate.py composition-pptx.json pptx.schema.json
.venv/bin/python validate.py composition-web.json web.schema.json
.venv/bin/python render_pptx.py composition-pptx.json out-pptx.pptx
.venv/bin/python render_web.py composition-web.json out-web.html
```
