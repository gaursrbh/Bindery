# Bindery M3 — Build-Ready Spec

Resolves the three decision tickets on the [Bindery M3 build-ready spec map](https://github.com/gaursrbh/Bindery/issues/23)
(issues #24-#26) into a concrete spec for M3: **token compliance linter
(R6), lockfile round-trip (R8), artifact library (R9)**.

Charted and worked autonomously (user offline, per explicit instruction).
**Preview rasterization (LibreOffice headless) is scoped out of this pass** —
`soffice` isn't installed, and installing a ~1GB+ system dependency
unilaterally while the user is offline is a heavier action than appropriate.
mainPRD itself ranks the linter above it anyway.

## 1. Decisions carried forward

| # | Question | Answer | Source |
|---|---|---|---|
| 1 | Linter mechanism | PPTX: walk python-pptx shapes/runs, compare color/size/font against `ds.tokens`' flattened value set. Web: regex-scan rendered HTML outside the `tokens.css` `:root{}` block for literal hex/px. New `bindery lint`, exit 7. | issue #24 |
| 2 | Lockfile | mainPRD §6.6 shape + a `composition` field (self-sufficient to re-render). New `bindery rerender`. PPTX byte-identical; web best-effort only (documented gap). | issue #25 |
| 3 | Artifact library | Filesystem JSON index, not SQLite (no GUI to justify it yet). `bindery list`/`show`/`rerender`. | issue #26 |

## 2. Token compliance linter

Package: `bindery/lint/`.

### 2.1 Interface

```python
@dataclass
class LintViolation:
    location: str    # e.g. "slide 0 / shape 2 / run 0" or "line 42"
    kind: str         # "color" | "font-size" | "font-family"
    value: str

def lint(artifact_path: Path, ds: DesignSystem, target: str) -> list[LintViolation]:
    """Dispatches to bindery/lint/pptx.py or bindery/lint/web.py by target."""
```

### 2.2 PPTX (`bindery/lint/pptx.py`)

Opens the rendered `.pptx` with `python-pptx`. For every shape's text frame,
every paragraph, every run: collect `run.font.color.rgb` (as `#RRGGBB`),
`run.font.size` (pt), `run.font.name`. Build the allowed-value set once from
`ds.tokens` (every `value` field across every category, flattened). Anything
not in that set is a `LintViolation`.

### 2.3 Web (`bindery/lint/web.py`)

Reads the rendered `.html`. Locates the `<style>` (or inline `:root{...}`)
block written by `render/web.py`'s `_tokens_css` — everything inside it is
exempt (it's the token *definitions*, not usage). Regex-scans the rest of the
file for `#[0-9a-fA-F]{3,6}` and bare `\d+(px|pt)` occurrences; each is a
`LintViolation` with the surrounding line as location.

### 2.4 CLI

```
bindery lint <artifact.pptx|.html> --ds <name@version> [--ds-root <path>]
```

Prints each violation to stderr, one per line. Exit 0 if none, exit 7 if any
found (extends M1/M2's exit-code sequence: 5=`PlannerError`,
6=`WebBuildError`, 7=lint violations present).

## 3. Lockfile

Package: `bindery/lock.py`.

### 3.1 Format (mainPRD §6.6, extended)

```json
{
  "design_system": "reference@1.0.0",
  "design_system_hash": "sha256:...",
  "renderer": "pptx@0.1.0",
  "models": {"planner": "qwen2.5:7b-instruct-q4_K_M"},
  "seed": 42,
  "schema": "bindery/v1",
  "created": "2026-08-16T20:00:00Z",
  "composition": { "...": "the full resolved Composition IR" }
}
```

`models`/`seed` are `{}`/`null` for the `generate` path (no Planner
involved). `composition` is mandatory — the lock must be self-sufficient to
re-render without the original brief or composition file still existing.

### 3.2 Hashing

```python
def hash_design_system(ds_path: Path) -> str:
    """sha256 over sorted (relative_path, file_bytes) pairs under ds_path,
    excluding node_modules/ and renderer-generated files
    (.bindery-entry.jsx, tokens.css)."""
```

### 3.3 Writing

`bindery/cli.py`'s `_generate`/`_plan` write `<out>/<stem>.lock.json`
alongside the artifact on every successful render (mainPRD §7 step 7,
"Bind"), after the artifact, before the index entry (§4.3).

### 3.4 Re-render from lock

```
bindery rerender <lock.json> --out <dir>
```

Resolves the DS by the lock's exact version, recomputes
`design_system_hash`, errors (`DesignSystemError`) if it doesn't match the
lock's recorded hash, then calls the target's `render()` with the lock's
stored `composition`. **PPTX**: output is byte-identical (python-pptx is
deterministic given identical inputs). **Web**: content-identical only —
Vite's bundler can introduce non-deterministic ordering/hashing in its
output; this is a real, documented gap in R8's "byte-identical" claim for
the web target, not silently accepted.

## 4. Artifact library

Package: `bindery/library.py`.

### 4.1 Index format

`<out-root>/.bindery-index.json` — a JSON array, one entry per artifact:

```json
{
  "id": "a1b2c3d4",
  "path": "deck.pptx",
  "lock_path": "deck.lock.json",
  "target": "pptx",
  "design_system": "reference@1.0.0",
  "created": "2026-08-16T20:00:00Z"
}
```

`id` is the first 8 hex chars of a sha256 over `(path, created)`.

### 4.2 CLI

```
bindery list --out <dir>
bindery show <id> --out <dir>
bindery rerender <id-or-lock-path> --out <dir>
```

`list` prints a table (id, target, ds, created). `show` prints one entry's
full detail (paths, composition summary). `rerender` accepts either an
index id (looked up against `.bindery-index.json` in `--out`) or a direct
path to a `.lock.json` file (§3.4).

### 4.3 Indexing

Every successful `generate`/`plan` call appends one entry to
`<out>/.bindery-index.json` after writing the lock file.

## 5. What M3 explicitly does not build

- Preview rasterization (LibreOffice headless) — needs a system-level
  install decision, deferred to the user.
- VLM critique (mainPRD §7 step 6) — P1, explicitly optional.
- SQLite artifact index — JSON index instead (issue #26); SQLite is the
  natural upgrade once a GUI (M4) justifies a real query layer.

## 6. File/task breakdown for M3

```
bindery/
  lint/
    __init__.py        # lint() dispatch — §2.1
    pptx.py             # §2.2
    web.py               # §2.3
  lock.py                # hash_design_system(), write_lock(), read_lock() — §3
  library.py              # index read/write/append, id generation — §4.1
  cli.py                   # +lint, +rerender, +list, +show subcommands;
                            # _generate/_plan write lock + index entry

tests/
  test_lint_pptx.py
  test_lint_web.py
  test_lock.py            # hash stability, round-trip write/read
  test_rerender.py         # pptx byte-identical; web content-identical
  test_library.py          # index append/list/show
  test_cli_lint_lock_library.py
```
