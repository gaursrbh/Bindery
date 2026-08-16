# Bindery — Product Requirements Document

**A local-first design artifact studio for macOS**

| | |
|---|---|
| **Version** | 0.1 (draft) |
| **Date** | 15 August 2026 |
| **Status** | For review |
| **Author** | Saurabh |

---

## 0. Naming

**Bindery** — the room in a print shop where loose pages become finished, bound objects.

Why it fits:

- It is a **workshop**, not a canvas. You bring content; it comes back as a finished thing. That is exactly the interaction model.
- A bindery handles **many formats** from one set of house standards — books, pamphlets, portfolios. Maps cleanly onto decks, pages, and infographics sharing one design system.
- **"Binding" is also the core technical concept.** Every artifact is *bound* to a specific design system version, renderer version, and model. The lockfile is literally called `bindery.lock`. The metaphor and the architecture are the same word, which is rare and worth taking.
- Short, pronounceable, no dominant software trademark. (`bindery.app`, `bindery.dev` worth checking; a minor `bindery.js` library exists but is dormant and in a different category.)

**Shortlist of alternates**, in case Bindery doesn't land:

| Name | Angle | Risk |
|---|---|---|
| **Signet** | A seal — stamping house identity onto a document | Slightly formal/heraldic |
| **Kiln** | Raw material in, fired artifact out; local heat | Old Fog Creek product of the same name |
| **Rendition** | A versioned interpretation of a work; puns on "render" | Three syllables, less punchy |
| **Verso** | The left-hand page; quiet, typographic | Verso Books; may read as too literary |
| **Compositor** | The person who set type before printing | Long; overloaded in graphics/OS contexts |

The rest of this document uses **Bindery**.

---

## 1. Problem Statement

Producing on-brand design artifacts — decks, one-pagers, infographics, microsites — currently forces a choice between three bad options: hand-building each one (hours per artifact, and consistency degrades as volume rises), using a cloud AI tool (fast, but generic output, no persistent design system, and content leaves the machine), or scripting one-off generators (consistent, but brittle and rebuilt from scratch per project).

The person affected is a practitioner who produces **many** artifacts across **multiple distinct visual identities** — different clients, business lines, or audiences — where drift between them is a real cost and where the source content is often sensitive enough that cloud tools are a non-starter.

The cost of not solving it: artifact production stays a linear function of hours worked, visual consistency erodes silently over time, and existing design-token work gets re-implemented per project instead of compounding into an asset.

---

## 2. The Core Insight

> **The model writes the specification. The renderer draws the pixels.**

This is the architectural decision everything else follows from, and it is what separates Bindery from prompting a chat model for a deck.

A language model asked to emit PPTX XML, or raw CSS, or a finished SVG, will produce something *plausible* and *off-brand*. It will invent a hex value one shade off. It will pick a font that isn't in the stack. It will nudge a margin. These errors are individually trivial and collectively fatal to a design system.

So the model is never allowed to emit final-form output. It emits a **validated JSON intermediate representation (IR)** describing *intent* — "title slide, eyebrow text X, headline Y, supporting stat Z, accent variant 2." A deterministic renderer consumes that IR and draws it using components from the pinned design system. The model cannot express an off-palette color because the schema has no field for a color.

Consequences:

- Design system compliance becomes **structurally guaranteed**, not prompted-for and hoped-for.
- A weaker local model becomes sufficient, because the hard part (pixel-accurate layout) is deterministic code, not generation.
- Output is **reproducible**: same IR + same lock = same bytes.
- Swapping the design system on an existing artifact is a re-render, not a regeneration.

---

## 3. Goals

1. **Time to first usable artifact under 3 minutes** for a standard request against an existing design system — measured from brief submission to a file you'd send without editing, on a warm model.
2. **Design system compliance at 100% by construction** — zero off-token colors, fonts, or spacing values in rendered output, verified by an automated linter on every render, not by eye.
3. **Reproducibility** — re-running any artifact from its `bindery.lock` reproduces it exactly, months later, on a different machine with the same assets.
4. **Design systems compound** — adding the second, third, and tenth artifact to a design system costs progressively less, because components accumulate. Target: DS #1 takes a day to author; artifact #20 in that system takes minutes.
5. **Nothing leaves the machine** — full functionality with the network interface disabled. This is a hard requirement, not a preference, and it is testable.

---

## 4. Non-Goals

| Non-goal | Why |
|---|---|
| **A design tool** — no canvas, no direct manipulation, no drag-to-resize | Figma exists and is better at it. Bindery's value is *generation under constraint*. Adding a canvas invites people to break the design system by hand, which destroys the core guarantee. Editing happens by amending the brief and re-rendering, or by opening the output in its native app. |
| **Authoring design systems from a blank page in v1** | Import and codify an existing identity first. Generative brand creation is a separate, harder product. v1 ships with an importer and 2–3 reference systems. |
| **Cloud or hybrid inference** | The privacy guarantee is only meaningful if it is absolute. A "just this once, use the API" escape hatch makes the whole claim conditional. If a task genuinely needs a frontier model, the user does that elsewhere and pastes the result in as source content. |
| **Multi-user, sharing, collaboration, a server** | Single-user local app. Design systems are git-versioned directories — that *is* the collaboration story, and it's free. |
| **Video, animation, 3D, print-production PDF (bleeds, spot color, imposition)** | Different toolchains, different quality bars, no shared architecture. Parking lot. |
| **Being a general chat interface** | There are a dozen good local chat apps. Bindery has a chat surface only in service of a brief. |

---

## 5. Users & User Stories

### Persona A — The Producer (primary; ~90% of sessions)

Has a design system already. Needs artifacts out the door.

- As a Producer, I want to paste a rough outline and get a deck in a named design system, so that I stop rebuilding the same title-and-agenda slides.
- As a Producer, I want to point at a CSV and get charted slides using my palette, so that data and design stay in sync without manual restyling.
- As a Producer, I want to re-render an existing artifact into a *different* design system, so that the same content can serve two audiences without a rebuild.
- As a Producer, I want to regenerate one section of a deck while everything else stays byte-identical, so that a small revision doesn't reshuffle the whole file.
- As a Producer, when a render fails or the model produces something malformed, I want a clear error naming what broke and a one-click retry, so that I'm not debugging a black box.
- As a Producer, I want to run the same brief from the command line, so that artifact generation can sit inside an existing scripted pipeline.

### Persona B — The System Steward (occasional but high-leverage)

Owns the visual identity. Sessions are rarer but shape everything the Producer does.

- As a Steward, I want to define tokens once and have every renderer consume them, so that a palette change propagates to decks, pages, and infographics in one edit.
- As a Steward, I want to version a design system semantically, so that a breaking layout change doesn't silently alter last quarter's artifacts.
- As a Steward, I want to add a component (a new slide layout, a new card variant) and have it immediately available to the planner, so that the system grows from real use rather than up-front specification.
- As a Steward, I want to see which artifacts are pinned to an outdated DS version, so that I can decide what to migrate.

### Persona C — The Tinkerer (you, on a Sunday)

- As a Tinkerer, I want to swap which local model handles which role, so that I can trade speed against quality per task.
- As a Tinkerer, I want to see the exact IR the model produced before it renders, so that I can debug prompts and schemas directly.

---

## 6. Core Concepts & Data Model

Six objects. Everything in the product is one of these.

### 6.1 Brief
The request. Natural language plus optional structured attachments.

```yaml
intent: "Board update on Q3 program performance"
target: pptx              # pptx | web | infographic
design_system: acme@2.1.0 # resolved to exact version at bind time
sources:
  - path: ./q3-metrics.csv
  - path: ./notes.md
constraints:
  max_slides: 12
  audience: executive
  tone: measured
  must_include: ["enrollment trend", "cost per member"]
```

### 6.2 Design System
A **versioned directory**, git-friendly, human-editable. Not a database row.

```
design-systems/acme/
├── system.yaml              # name, semver, description, target support
├── tokens.json              # W3C Design Tokens format — colors, type, space, radii
├── typography/              # font files + licensing note
├── assets/                  # logos, marks, textures, icon set
├── components/
│   ├── pptx/                # slide layouts as templates + Python layout fns
│   │   ├── title.py
│   │   ├── stat-trio.py
│   │   └── _layouts.potx
│   ├── web/                 # component library pinned to a version
│   │   ├── package.json     # e.g. react 18.3.1, tailwind 3.4.x — pinned exactly
│   │   └── src/
│   └── svg/                 # infographic primitives
├── rules/
│   ├── layout.md            # grid, spacing scale, density guidance
│   ├── content.md           # voice, capitalization, number formatting
│   └── forbidden.md         # what this system never does
└── schema/
    └── overrides.json       # DS-specific extensions to the IR schema
```

**On UX library versioning** (an explicit requirement): each design system pins its own dependency set — its own React version, its own Tailwind config, its own chart library. Systems do not share a global `node_modules`. Web renders execute in an isolated, per-system dependency tree so that `acme@2.1.0` can sit on React 18 while `northstar@1.0.0` sits on React 19 without either breaking. This costs disk space and buys the ability to reproduce a two-year-old artifact.

### 6.3 Composition (the IR)
Validated JSON. The contract between the generative and deterministic halves.

```json
{
  "schema": "bindery.pptx/v1",
  "design_system": "acme@2.1.0",
  "blocks": [
    {
      "component": "title",
      "props": {
        "eyebrow": "Q3 2026",
        "headline": "Enrollment up 12%, cost per member flat",
        "accent": "primary"
      }
    },
    {
      "component": "stat-trio",
      "props": {
        "stats": [
          {"value": "142,300", "label": "Members enrolled", "delta": "+12%"},
          {"value": "$412", "label": "Cost per member", "delta": "0%"},
          {"value": "94.2%", "label": "Retention", "delta": "+1.4pt"}
        ]
      }
    }
  ]
}
```

Note what the model *cannot* say here: no colors, no coordinates, no font sizes, no pixel values. `"accent": "primary"` is an enum the design system defines. This is the enforcement mechanism.

### 6.4 Renderer
Target-specific, deterministic, pure. `(Composition, DesignSystem) → Artifact`. Same inputs always produce the same output. No network, no clock, no randomness.

### 6.5 Artifact
The output file(s) plus a manifest — source brief, resolved composition, render duration, lint results, preview rasters.

### 6.6 Binding (`bindery.lock`)
The reproducibility record.

```json
{
  "design_system": "acme@2.1.0",
  "design_system_hash": "sha256:9f2a...",
  "renderer": "pptx@0.4.2",
  "models": {
    "planner": "qwen3:34b-instruct-q5",
    "writer":  "llama3.3:8b-q8",
    "critic":  "llama3.2-vision:11b"
  },
  "seed": 42,
  "schema": "bindery.pptx/v1",
  "created": "2026-08-15T14:22:03Z"
}
```

---

## 7. The Router — Deterministic vs. Generative

You framed this as "Python **or** local LLM." In practice the interesting cases are **both, in sequence**. The router's job is deciding which sub-task goes where, and it should be driven by a simple test: *does this step have a single correct answer?*

| Step type | Path | Examples |
|---|---|---|
| **Deterministic only** | Python/Node, no model | Tokens → CSS variables. CSV → chart geometry. Number and date formatting. Format conversion. Template fill with supplied values. Contrast-ratio checks. Text overflow measurement. |
| **Generative only** | Local model | Narrative structure. Headline and body copy. Section ordering. Icon and imagery selection from a fixed set. Alt text. Summarizing source material. |
| **Hybrid — the default** | Model plans → schema validates → code renders → critic reviews | Nearly every real artifact request. |

### The standard pipeline

```
Brief
  ↓
[1] Ingest            deterministic   parse sources, extract tables, chunk text
  ↓
[2] Plan              generative      structure → Composition IR
  ↓
[3] Validate          deterministic   JSON Schema; component & prop existence;
                                      content length vs. measured capacity
  ↓  ←──── repair loop, max 3 attempts, errors fed back as structured messages
[4] Render            deterministic   IR + DS → artifact file
  ↓
[5] Lint              deterministic   off-token values, contrast, overflow, orphans
  ↓
[6] Critique          generative      VLM on rasterized preview — density,
                                      hierarchy, balance                [optional]
  ↓
[7] Bind              deterministic   write artifact + manifest + lock
```

**Step 3 is where most of the value is.** Schema validation catches the model's errors before they become pixels, and the validation errors are fed back as structured repair instructions rather than "try again." A 14B model with a tight repair loop beats a 70B model without one, and runs five times faster.

**Step 5 (deterministic lint) matters more than step 6 (VLM critique).** A linter that greps rendered output for hex values outside the palette is fast, free, and never wrong. A vision model asking "does this look good?" is slow, expensive, and frequently wrong. Ship the linter first; treat the critic as a v1.1 nicety.

### Escape hatch: freeform generation
For genuinely novel infographics with no matching component, the router may fall through to code generation (model emits SVG or a React component directly). This output is quarantined — flagged as unbound, excluded from the compliance guarantee, and surfaced to the Steward as a candidate for promotion into the design system. **The healthy loop is that freeform output becomes a component, and the next request hits the fast path.**

---

## 8. Local Model Layer

Roles, not a single model. Small models handle most of it.

| Role | Job | Size class | Notes |
|---|---|---|---|
| **Planner** | Brief → Composition IR | 14–34B instruct | The quality-critical one. Needs reliable structured output. |
| **Writer** | Headlines, body copy, labels | 8–14B | Called often; latency matters more than depth. |
| **Coder** | SVG/React for freeform escape hatch | 14–34B coder-tuned | Only on the fallback path. |
| **Critic** | Visual review of rasterized preview | Vision, 11B+ | Optional, off by default. |
| **Embedder** | Retrieval over DS docs + prior artifacts | Small embedding model | For "make it like the March deck." |

### Runtime

As of mid-2026, <cite index="9-1">Ollama switched to a native MLX runner on Apple Silicon in version 0.19 (March 2026), so on a modern Mac it is no longer a llama.cpp wrapper</cite> — which makes it a reasonable default backend rather than a compromise. <cite index="1-1">MLX has pulled ahead of llama.cpp on Apple Silicon, roughly 30–60% faster on most workloads on M5 hardware</cite>, so MLX-LM directly remains the option for maximum throughput.

**Recommendation:** abstract behind an OpenAI-compatible client so Ollama, LM Studio, and a direct MLX-LM server are interchangeable. Ship with Ollama as the default (easiest install path, one command per model).

Worth evaluating separately: <cite index="3-1">Apple's Foundation Models framework, which matured through 2026 and provides type-safe structured output via the `@Generable` macro, with built-in tool calling and stateful multi-turn sessions</cite>. For the Planner role specifically — where guaranteed schema conformance is the entire requirement — a native guided-generation path may outperform prompt-and-validate. Flagged as an open question rather than a v1 dependency, since it constrains you to Swift and a recent macOS.

**Structured output is a hard requirement, not a prompt technique.** Use grammar-constrained decoding (GBNF) or JSON-schema-enforced sampling. Do not rely on asking nicely and parsing.

**Memory budget:** rough current guidance is <cite index="7-1">16GB → a ~14B-class model; 36GB → 8–14B comfortably; 64GB → 34B; 128GB → 70B</cite>. Practically: on a 36–64GB machine, run one loaded model at a time and accept swap latency between roles, or keep Writer resident and load Planner on demand. On 128GB, keep Planner and Writer both resident. This drives the concurrency design — assume **one** model in memory unless the machine is large.

---

## 9. Requirements

### P0 — Must have for v1

| # | Requirement | Acceptance criteria |
|---|---|---|
| **R1** | Brief intake — text + file attachment (md, csv, xlsx, docx, txt) | Given a brief and a CSV, when submitted, then parsed content appears in the ingest preview with detected tables listed. |
| **R2** | Design system registry — load, list, validate, resolve version | Given a malformed `system.yaml`, when loading, then a specific error names the file and field. Given `acme@2.x`, then it resolves to the highest matching installed version and records the exact version in the lock. |
| **R3** | Composition IR with JSON Schema validation | Given a model output referencing a nonexistent component, when validated, then it fails with a message listing available components, and the repair loop retries up to 3 times before surfacing failure. |
| **R4** | PPTX renderer | Given a valid composition, when rendered, then a `.pptx` opens in Keynote and PowerPoint without repair prompts, and every text frame fits without overflow. |
| **R5** | Web renderer — single-file HTML output | Given a valid composition, when rendered, then a self-contained `.html` (inlined CSS/JS/fonts) renders identically offline in Safari and Chrome. |
| **R6** | Token compliance linter | Given rendered output, when linted, then any color, font family, or spacing value not traceable to `tokens.json` is reported with its location. Zero violations is the pass condition. |
| **R7** | Local model routing with per-role assignment | Given no network, when generating, then the pipeline completes. Given a configured role map, then each pipeline step calls its assigned model. |
| **R8** | `bindery.lock` written per artifact; re-render from lock | Given a lock file, when re-rendered on a clean machine with the same DS installed, then output is byte-identical for the deterministic path. |
| **R9** | Artifact library — browse, preview, re-open brief, re-render | Given a past artifact, when opened, then its brief, composition, lock, and preview are all visible and the brief is editable for re-run. |
| **R10** | CLI parity for generate and re-render | `bindery generate brief.yaml --ds acme@2.1.0 --out ./dist` produces the same result as the GUI. |

### P1 — Should have, fast follow

- **R11** Infographic/SVG renderer with a composable layout engine.
- **R12** VLM critic on rasterized previews, with a "regenerate section" action per finding.
- **R13** Design system importer — point at a Figma export, brand PDF, or existing deck; extract a candidate `tokens.json` for review.
- **R14** Cross-system re-render — retarget an existing composition to a different DS, with a diff of what couldn't map.
- **R15** Section-level regeneration with stable output for untouched sections.
- **R16** Chart module — CSV/dataframe → chart spec → DS-styled rendering, shared across all three targets.
- **R17** Watch mode — a directory of briefs renders on file change.

### P2 — Design for, don't build

- Component promotion workflow (freeform output → reviewed → committed as a DS component).
- Design system diffing and migration assistant across versions.
- DOCX and PDF report targets.
- Template marketplace / DS sharing as installable packages.
- Fine-tuning a small planner on your own accepted compositions.

*These are P2 specifically to constrain architecture now: the IR must be target-agnostic enough to add DOCX, and design systems must be self-contained enough to be distributable. Neither ships in v1.*

---

## 10. Technical Approach

### Recommended stack

| Layer | Choice | Rationale |
|---|---|---|
| **Core** | Python 3.12, packaged with `uv` | Where the rendering libraries live; matches your existing tooling. |
| **API** | FastAPI, localhost only, bound to 127.0.0.1 | Lets GUI and CLI share one engine. |
| **PPTX render** | `python-pptx`, with LibreOffice headless for preview rasters | You've done this loop before. LibreOffice QA previews catch layout breakage without opening PowerPoint. |
| **Web render** | Vite + `vite-plugin-singlefile`, per-DS isolated dependency tree | Known quantity; single-file output is the right artifact shape. |
| **SVG/infographic** | Programmatic SVG generation, `cairosvg`/`resvg` for raster export | Avoids a browser dependency for static output. |
| **Models** | Ollama (default) behind an OpenAI-compatible abstraction | Swappable for LM Studio or MLX-LM. |
| **Shell** | **v1: local web UI in the browser. v2: Tauri 2 wrapper.** | Do not build a Mac app shell in month one. Ship the engine, use it daily, wrap it once the workflow is stable. |
| **Storage** | SQLite for the artifact index; filesystem for everything substantive | Design systems and artifacts should be inspectable and git-versionable, not trapped in a database. |

### Sequencing

**Build the CLI first.** You live in a terminal, the CLI is the integration surface for any pipeline you already run, and it forces the engine to be properly headless. The GUI is a client of the same API. This ordering also means the product is useful to you in week three rather than month three.

### Milestones

| | Scope | Exit criterion |
|---|---|---|
| **M0** — Skeleton | IR schema, DS loader, one reference DS, PPTX renderer, CLI, no models (hand-written IR) | A hand-authored composition renders to a correct, on-brand deck. |
| **M1** — Generative | Planner integration, structured output, validation repair loop | A natural-language brief produces a usable deck without hand-editing the IR. |
| **M2** — Web target | Web renderer, per-DS dependency isolation, single-file output | Same brief renders to both a deck and a page from one composition. |
| **M3** — Quality | Token linter, preview rasterization, artifact library, lockfile round-trip | Zero lint violations across a 20-artifact regression corpus. |
| **M4** — Surface | Tauri shell, DS importer, infographic renderer | Someone who isn't you can install it and produce an artifact. |

---

## 11. Success Metrics

### Leading (measurable within weeks)

| Metric | Target | Stretch | How measured |
|---|---|---|---|
| Time to usable artifact | < 3 min | < 90 s | Timestamp brief submit → last accepted render |
| First-pass acceptance (no re-render needed) | 60% | 80% | Manual flag on artifact close |
| Composition validity on first model attempt | 85% | 95% | Schema validation pass rate before repair |
| Repair loop convergence within 3 attempts | 98% | 99.5% | Pipeline logs |
| Token lint violations per artifact | 0 | 0 | Linter output — this one is binary |
| Render step latency (deterministic only) | < 5 s | < 2 s | Instrumented |

### Lagging (months)

- **Artifacts per week produced through Bindery** vs. hand-built — the real adoption signal.
- **Component reuse rate** — % of blocks in new artifacts drawn from existing DS components rather than the freeform fallback. Should climb toward 90%+ as systems mature. *This is the single best health indicator for the whole product.*
- **Marginal cost curve** — median time for artifact #1 vs. #10 vs. #30 in a given design system. Should decline steeply.
- **Design system count in active use** — validates the multi-system premise, or falsifies it.

### Falsification criterion

If after 90 days of real use the reuse rate sits below 50% and the freeform escape hatch handles most requests, then the component-library premise is wrong and the product should be rebuilt around constrained code generation instead. Write this down now, check it honestly later.

---

## 12. Open Questions

**Blocking — resolve before M1**

1. **How is structured output enforced?** Grammar-constrained decoding via llama.cpp GBNF, Ollama's JSON-schema mode, or Apple Foundation Models' `@Generable`? This determines whether the planner is reliable enough to build on. *Owner: you. Spike it in a day against the real IR schema — it's the highest-risk unknown in the design.*
2. **What is the minimum viable planner size?** Test 8B / 14B / 34B against 20 representative briefs, scoring first-attempt schema validity and structural sensibility. If 14B suffices, the memory design gets much simpler and the app runs well on a 36GB machine.
3. **Does the IR generalize across targets, or does each target need its own schema?** A shared `bindery/v1` core with target-specific component vocabularies is the bet. Validate with one brief rendered to both PPTX and web before committing.

**Non-blocking**

4. Font licensing — can DS packages redistribute font files, or must they reference system-installed families? Affects portability of design systems.
5. How are design system *breaking* changes defined? Which layout modifications warrant a major version bump?
6. Should the web renderer's per-DS dependency isolation use pnpm workspaces, separate `node_modules`, or containerization? Disk cost vs. isolation strength.
7. Is Tauri the right shell, or is a menu-bar utility plus browser UI sufficient forever?
8. Multi-model memory management — evict-and-reload versus keeping one general model resident for all roles.

---

## 13. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Local planner can't produce reliable structured output** | High — kills the architecture | Grammar-constrained decoding; aggressive repair loop; fall back to a form-based brief that constructs IR semi-manually. Spike this first. |
| **Design system authoring is too laborious**, so only ever one system exists | High — the multi-system premise is the differentiator | Ship 2–3 strong reference systems; make forking one the primary path; the importer (R13) moves to P0 if this bites. |
| **Scope creep into a design tool** — "just let me nudge this one box" | High — destroys the compliance guarantee | The non-goal is written down. When it comes up, the answer is: open the output in Keynote. |
| **PPTX fidelity across PowerPoint/Keynote/Google Slides** | Medium | Regression corpus rendered and visually diffed on every renderer change; LibreOffice headless in CI. |
| **Per-DS dependency isolation bloats disk** (each system carrying its own React tree) | Medium | Content-addressed shared store with hard links; accept the cost — reproducibility is the point. |
| **Freeform escape hatch becomes the default path** | Medium | Track reuse rate as a first-class metric; make component promotion a low-friction workflow. |
| **The whole thing is over-engineered for one user's actual volume** | Medium | M0 is deliberately tiny and useful alone. If a hand-written IR plus a PPTX renderer covers 80% of the need, that is a legitimate stopping point. |

---

## 14. Timeline Considerations

No external deadline, which is itself a risk — this kind of project dies from unbounded M0. Suggested discipline:

- **Time-box the structured-output spike to two days.** If no reliable path exists, stop and redesign around form-based briefs before writing renderer code.
- **M0 must be usable alone.** If M0 ships and never reaches M1, hand-authored IR + a good PPTX renderer + design tokens is still a real improvement over the status quo. Design it to be a valid stopping point.
- **Dogfood between every milestone.** Produce five real artifacts before starting the next phase. The reuse-rate metric only means something if the artifacts are real.
- **Defer the Mac app shell to M4.** It is the most visible work and the least valuable. Resist it.

---

## Appendix A — Reference design systems to ship with v1

Three, chosen to stress different parts of the architecture:

1. **Clinical** — dense, data-heavy, conservative palette, high information density. Tests table and chart components and tight text-fitting.
2. **Editorial** — generous whitespace, strong typographic hierarchy, large imagery. Tests the layout engine's flexibility and asset handling.
3. **Utility** — near-brandless, high-contrast, accessibility-first. Tests the token system's floor and doubles as the accessibility regression baseline.

## Appendix B — Rejected alternatives

| Alternative | Why not |
|---|---|
| **Model generates final code directly** (SVG/HTML/OOXML) | Design system compliance becomes probabilistic. This is the thing that makes existing tools unusable for multi-brand work; reproducing it would be reproducing the problem. |
| **Template-only, no models** | Handles format but not content. The tedious part is writing and structuring, which is exactly where a model helps. |
| **Cloud models for planning, local for the rest** | The privacy guarantee becomes conditional and therefore worthless for sensitive content. |
| **Build on an existing agent framework** | The pipeline here is a fixed, mostly-deterministic DAG, not an open-ended agent loop. A framework would add abstraction over a well-understood control flow. |
| **Figma plugin instead of a standalone app** | Ties the product to a cloud tool, an API surface you don't control, and a canvas paradigm the architecture explicitly rejects. |