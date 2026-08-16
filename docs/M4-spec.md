# Bindery M4 — Build-Ready Spec

Resolves the three decision tickets on the [Bindery M4 build-ready spec map](https://github.com/gaursrbh/Bindery/issues/28)
(issues #29-#31) into a concrete spec for M4: **local web UI, infographic/SVG
renderer (R11), DS importer (R13)**.

Charted and worked autonomously (user offline, per explicit instruction).
**Tauri shell deferred** — Rust/Cargo not installed; mainPRD §10/§14
themselves prescribe local-web-UI-first anyway ("Do not build a Mac app
shell in month one"). **DS importer scoped to PPTX input only** — Figma/PDF
need new dependencies not yet justified.

## 1. Decisions carried forward

| # | Question | Answer | Source |
|---|---|---|---|
| 1 | Web UI | FastAPI (`bindery/server.py`, localhost-only) thin-wraps the engine; vanilla-JS static frontend; new `bindery serve`. | issue #29 |
| 2 | Infographic renderer | One `.py`/component returning an SVG fragment; new `schema/infographic.schema.json`; primary `.svg`, secondary `.png` via cairosvg. | issue #30 |
| 3 | DS importer | `bindery import <deck.pptx>` frequency-scans colors/fonts, writes `candidate-tokens.json` for review; no live DS auto-created. | issue #31 |

## 2. Infographic/SVG renderer

Package: `bindery/render/infographic.py`. Implements mainPRD R11.

### 2.1 Schema

`schema/infographic.schema.json` — same core-envelope + per-target-vocab
pattern as pptx/web. Reference DS ships 2 components: `stat-callout` (one
big number + label) and `title` (headline + optional eyebrow, same props
shape as pptx/web's title for consistency).

### 2.2 Component contract

```python
def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> str:
    """Returns an SVG fragment (a <g> element) positioned at (x, y) within
    `width`. Pure — no filesystem/network/randomness, same §6.4 discipline
    as pptx/web component code."""
```

### 2.3 Renderer

```python
def render(composition: dict, ds: DesignSystem, out_path: Path) -> RenderResult:
    """
    1. Validate against ds.effective_schemas["infographic"].
    2. Stack blocks vertically (same simple layout model M0's PPTX renderer
       uses), each block's layout() fragment placed at the next y-offset.
    3. Wrap fragments in one root <svg> sized from canvas tokens
       (token-driven width, height grows with content).
    4. Write the .svg (self-contained by construction — no external refs).
    5. Also render a .png alongside via cairosvg.svg2png (convenience
       preview, not the artifact of record — the .svg is canonical, same
       relationship M3's linter has to the rendered file it inspects).
    """
```

### 2.4 Reference DS

`design-systems/reference/components/infographic/{title,stat-callout}.py`,
`system.yaml` targets gains `infographic`.

## 3. Local web UI

Package: `bindery/server.py`, static assets in `bindery/static/`.

### 3.1 Endpoints

| Method | Path | Wraps |
|---|---|---|
| GET | `/design-systems` | `loader.list_installed()` |
| POST | `/generate` | `render` dispatch + lock/index write |
| POST | `/plan` | `plan_with_repair` |
| GET | `/artifacts` | `library.load_index()` |
| GET | `/artifacts/{id}` | `library.find_entry()` + lock detail |
| POST | `/artifacts/{id}/rerender` | CLI `rerender` logic |
| GET | `/lint` | `bindery.lint.lint()` |
| GET | `/artifacts/{id}/file` | serves the rendered file |

All business logic stays in `bindery/` core packages — the server is a thin
HTTP wrapper, no logic duplicated from the CLI.

### 3.2 Frontend

`bindery/static/index.html` — one page, vanilla JS, no build step: a form
(brief text, DS picker, target picker) posting to `/plan` or `/generate`,
and a table reading `/artifacts`. No React/Vite here — this is the app
shell, not a DS component library; mainPRD's non-goals explicitly reject a
canvas/design-tool surface, and a form + table doesn't need a frontend
framework.

### 3.3 CLI

```
bindery serve [--port 8420] [--out <dir>] [--ds-root <dir>]
```

Launches `uvicorn` programmatically, bound to `127.0.0.1` only.

## 4. DS importer

Package: `bindery/importer.py`.

### 4.1 Mechanism

```python
def scan_pptx(path: Path) -> ImportReport:
    """Walks every shape/paragraph in the deck (same traversal as
    bindery/lint/pptx.py), collecting font.color.rgb, font.size, font.name
    with frequency counts."""

@dataclass
class ImportReport:
    colors: dict[str, int]        # "#RRGGBB" -> occurrence count
    sizes: dict[int, int]          # pt -> occurrence count
    fonts: dict[str, int]           # family -> occurrence count
```

### 4.2 Candidate token proposal

Heuristic, not authoritative: most-frequent color -> `primary`, 2nd ->
`secondary`, 3rd -> `neutral`; most-frequent size -> `headline-size`. Written
as `<out>/candidate-tokens.json`, same shape as a real `tokens.json`.
Frequency report printed to stdout for human judgment — the tool proposes,
a Steward decides (mainPRD persona B).

### 4.3 CLI

```
bindery import <deck.pptx> --out <dir>
```

Does not create a `design-systems/<name>/` directory or install anything —
components and rules still need human authoring; this is token intake only.

## 5. What M4 explicitly does not build

- Native Tauri shell (deferred, mainPRD's own "v2" per §10/§14).
- Figma export / brand PDF import (R13's other two input types).
- A GUI canvas/design surface (mainPRD §4 non-goal, unconditionally).

## 6. File/task breakdown for M4

```
bindery/
  render/
    infographic.py        # §2.3
  server.py                 # §3.1
  static/
    index.html               # §3.2
  importer.py                # §4.1-4.2
  cli.py                       # +serve, +import subcommands

schema/
  infographic.schema.json

design-systems/
  reference/
    components/infographic/
      title.py
      stat-callout.py

tests/
  test_render_infographic.py
  test_server.py               # FastAPI TestClient, no real network
  test_importer.py
```
