# Bindery M2 — Build-Ready Spec

Resolves the two decision tickets on the [Bindery M2 build-ready spec map](https://github.com/gaursrbh/Bindery/issues/19)
(issues #20-#21) into a concrete spec for M2: **web renderer, per-DS
dependency isolation, single-file HTML output** — the same composition
renders to both a deck and a page (mainPRD §10, Milestones table).

Charted and worked autonomously (user offline, per explicit instruction to
proceed through M1/M2/M3). `schema/web.schema.json` already existed (issue #4's
IR-generalization spike) — 3 components (`title`, `stat-trio`, `nav-bar`),
asymmetric vs. pptx's 4, deliberately (issue #4).

## 1. Decisions carried forward

| # | Question | Answer | Source |
|---|---|---|---|
| 1 | Build mechanism | Per-DS Vite project (`components/web/`), one `.jsx` per component, `npm install` a one-time setup step (fail fast if `node_modules` missing). Render generates a temp entry embedding composition+tokens as static data, runs `npm run build` via subprocess (vite-plugin-singlefile inlines everything), copies the single HTML file out. | issue #20 |
| 2 | Token → CSS | `tokens.json` → generated `tokens.css` custom properties (`var(--token-name)`), never literal hex/px in component code. Tailwind descoped for M2. | issue #21 |

## 2. Web renderer

Package: `bindery/render/web.py`. Implements mainPRD R5.

### 2.1 Interface

```python
def render(composition: dict, ds: DesignSystem, out_path: Path) -> RenderResult:
    """
    1. Validate composition against ds.effective_schemas["web"] (same pattern
       as render/pptx.py's _validate).
    2. Confirm design-systems/<name>/components/web/node_modules exists;
       raise DesignSystemError if not (fail fast, same as M0's missing-
       layout-module check — `npm install` is a DS-setup step, not run here).
    3. Generate tokens.css from ds.tokens (one --custom-property per token).
    4. Generate a temp entry (.bindery-entry.jsx) in the DS's web dir:
       imports each block's component module, renders them in composition
       order inside a root App component, embeds composition.blocks[*].props
       and ds.tokens as static JS literals (no runtime fetch — required for
       genuinely offline single-file output).
    5. Run `npm run build -- --outDir <tmpdir>` via subprocess in the DS's
       web dir, with vite.config.js pointing build.rollupOptions.input at
       the generated entry and using vite-plugin-singlefile. Non-zero exit
       -> WebBuildError(stderr).
    6. Copy the single resulting .html to out_path; delete the generated
       entry + tmp build dir.
    """
```

### 2.2 Component → module contract (`design-systems/<name>/components/web/src/components/*.jsx`)

```jsx
export default function Title({ props, tokens }) {
  return (
    <div style={{ color: "var(--color-primary)" }}>
      {props.eyebrow && <p className="eyebrow">{props.eyebrow.toUpperCase()}</p>}
      <h1>{props.headline}</h1>
    </div>
  );
}
```

One module per component, default export, `({ props, tokens }) => JSX`.
`tokens` is passed through for components needing it beyond CSS vars (e.g. a
font-family lookup); most styling should reference `var(--...)` directly.

### 2.3 Per-DS web directory contract

```
design-systems/<name>/components/web/
├── package.json      # pins react, react-dom, vite, @vitejs/plugin-react,
│                      # vite-plugin-singlefile — exact versions
├── vite.config.js     # build.rollupOptions.input set per-render by the
│                      # renderer (env var or generated override file)
├── node_modules/      # `npm install`, run once, out of band — not by bindery
└── src/
    └── components/
        ├── title.jsx
        ├── stat-trio.jsx
        └── nav-bar.jsx
```

### 2.4 Errors

`bindery/render/errors.py` gains `WebBuildError(stderr: str)`, alongside the
existing `CompositionError`/`RenderError` (which stay PPTX-specific — a page
reflows rather than overflowing a fixed frame, so there's no direct
overflow-check analogue for web; the build step itself is the deterministic
failure point).

## 3. What M2 explicitly does not build

- Tailwind / utility-class styling (issue #21) — plain CSS custom properties.
- Token-compliance linting (mainPRD R6) — M3.
- Cross-target composition validation (same composition object literally
  reused for both targets) — M2's exit criterion is "the same *composition
  content*, expressed as two target-appropriate compositions, renders to
  both," not byte-identical IR reuse across targets (pptx and web vocabs are
  intentionally asymmetric, issue #4).

## 4. File/task breakdown for M2

```
bindery/
  render/
    web.py             # render() — §2.1
    errors.py           # +WebBuildError — §2.4

design-systems/
  reference/
    components/web/
      package.json
      vite.config.js
      src/components/
        title.jsx
        stat-trio.jsx
        nav-bar.jsx

tests/
  test_render_web.py    # one composition per component; missing node_modules
                          # -> DesignSystemError; build failure -> WebBuildError
```

## 5. Reproducing / starting point

`spike/composition-web.json` already has a valid two-block web composition
(needs `design_system` retargeted from `acme@2.1.0` to `reference@1.0.0` to
render against M0/M1's reference DS, same adjustment M1's dogfooding needed).
Build order: `package.json` + `npm install` first (nothing renders without
`node_modules`), then the three component modules (parallel, independent of
each other), then `bindery/render/web.py` (depends on both).
