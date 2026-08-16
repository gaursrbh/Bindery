# Design system dimensions & component-vocabulary growth

Two related authoring disciplines, written down once so future design
systems and future components follow a consistent process instead of
one-off improvisation each time.

## 1. Dimensions for authoring a new design system

`reference` and `editorial` were each built by ad-hoc, one-off construction
— no shared vocabulary for *what actually varies* between two design
systems. Inspired by (not copied from — see issue #39) `baoyu-slide-deck`'s
17 presets, each a named point in a 4-dimension space (texture / mood /
typography / density): Bindery's own equivalent dimensions, in terms of the
primitives that actually exist in `tokens.json` and a DS's component code.

| Dimension | What it controls | Range observed so far |
|---|---|---|
| **Palette temperature** | `color.primary`/`secondary` hue family | cool navy (`reference`) vs. warm terracotta-on-cream (`editorial`) |
| **Spacing density** | box heights, margins, gaps between stacked blocks | tight (`reference`'s 0.6in margins) vs. generous (`editorial`'s 1.0in margins, larger row gaps) |
| **Typographic voice** | `typography.family`, weight, whether a headline is serif/sans | sans/bold (`reference`) vs. serif/bold with a thin accent-rule hierarchy marker (`editorial`) |
| **Decorative motif** | whether components use a signature mark (a rule, a bullet-dot vs. em-dash, etc.) or stay unornamented | `reference` has none; `editorial` has a consistent thin-rule-under-eyebrow motif reused across `title` and `stat-trio` |

When starting the next design system (Clinical or Utility, per mainPRD
Appendix A), pick a point on each of these four axes *before* writing any
component code — the same way `editorial` was scoped in conversation before
implementation started. This doesn't replace judgment, it just makes the
starting brief for a new DS four questions instead of a blank page.

## 2. Component-vocabulary growth discipline

From issue #42, applied concretely in issue #40's classification of all 21
`baoyu-infographic` layout types before building anything: **a new named
"thing" is not automatically a new component.** Before adding one, ask:

> Can an existing component's `props` already express this, or does this
> structurally need a new layout grammar?

Issue #40's classification is the worked example:

- **New component** (8 built, issues #44-51): each of these needs a
  genuinely different SVG/layout structure — a pyramid is not a prop
  variant of a bar chart.
- **Reuse, no new component**: `bento-grid`/`dashboard`/`dense-modules` are
  all "arrange existing components in a grid" — a layout-container
  capability, not a new component. `winding-roadmap` is `linear-progression`
  with a curved path, a rendering detail not a structural difference.
- **Out of scope**: illustration-heavy types (`comic-strip`, `isometric-map`,
  etc.) that don't fit the deterministic SVG-fragment-from-structured-data
  model without substantial custom rendering work per type — ruling
  something out of scope is different from either of the above, and belongs
  in a map's "Out of scope" section, not silently dropped.

Apply this same three-way test (new component / reuse via props / out of
scope) to every future vocabulary expansion — pptx, web, infographic,
html-slides alike — not just the one baoyu-inspired batch.
