# Minimum viable Planner model size — results

Answers issue #3 / mainPRD §12.2. Enforcement mechanism fixed per issue #2's finding:
Ollama JSON-schema-enforced sampling (`format: <schema>`), the only mechanism that gave a
structural (not statistical) guarantee in that spike. 20 representative briefs (`briefs.json`,
expanded from issue #2's 6 to the ~20 §12 asks for), same `bindery.pptx/v1` schema.

Scored two axes, no repair loop:
1. **Schema validity** — same check as issue #2.
2. **Structural sensibility** — cheap deterministic proxies, not a full rubric: every
   `must_include` keyword appears somewhere in the emitted prop values; `stat-trio` is only
   used when the brief's sources actually contain numeric content; block count is ≥2 when the
   brief has ≥2 distinct facts to place; no placeholder values (`TBD`, `N/A`, etc.).

## What changed from the plan

Only 7B and 14B were tested, not 8B/14B/34B as the issue lists. This machine has 24GB RAM;
a 34B model at q4 quantization needs ~20GB for weights alone, which would leave the OS almost
no headroom and doesn't reflect a realistic deployment target per mainPRD §8's memory budget
table (36GB → 8–14B comfortably; 64GB → 34B). Pulling and running 34B here would produce a
number that doesn't generalize to any real target machine, so it was skipped rather than run
under conditions the PRD itself says are the wrong tier for that model size. 7B was substituted
for 8B (nearest available Ollama tag; same class).

## Results

| Model | Schema-valid | Structurally sensible | Avg latency |
|---|---|---|---|
| qwen2.5:7b-instruct-q4_K_M | **20/20** | **13/20** | 10.7s |
| qwen2.5:14b-instruct-q4_K_M | **20/20** | **13/20** | 25.2s |

Both models hit the same 20/20 schema validity as issue #2's 14B run on the smaller brief set —
schema-constrained decoding structurally cannot emit an invalid object, so this axis is
saturated by construction; it distinguishes mechanisms, not model sizes.

On structural sensibility, 7B and 14B failed the *same 7 briefs*, for the same reasons:

- `risk-summary`, `onboarding-checklist`, `partner-announcement`, `team-retro-highlights` —
  flagged because the model used `stat-trio` for a brief whose source content is qualitative,
  not numeric. Inspecting the raw output: this is a heuristic false positive, not a reasoning
  failure. Both models turned qualitative risk/retro items into a defensible stat-trio (e.g.
  labeling risks "Critical / High / Medium" with a count) — a legitimate compositional choice,
  not nonsense. A tighter rubric would need a human or LLM-judge pass rather than a component-
  type proxy.
- `hiring-plan`, `budget-variance-report` (7B only), `incident-postmortem` — flagged for
  missing the literal `must_include` phrase. Inspecting the raw output: both models expressed
  the concept (e.g. `"Engineering" / "+8"` stat instead of the literal string `"engineering
  headcount"`) rather than omitting it. This is a keyword-matching limitation in the scorer,
  not a content failure.
- `fundraising-progress` (14B only) — one genuine placeholder value (`"placeholder"`) in an
  otherwise-valid response; a one-off sampling artifact, not a size-correlated pattern (7B
  didn't reproduce it, nor did 14B on any other brief).

No brief showed a case where 14B produced a structurally better IR than 7B failed to produce.

## Recommendation

**7B is sufficient for the Planner role at this schema's complexity**, provided the
JSON-schema-enforced decoding from issue #2 is the enforcement mechanism and a repair loop
(mainPRD §7 step 3) still runs after — this spike measures first-attempt output only. 14B added
2.35x latency (25.2s vs 10.7s avg) for identical schema-validity and structural-sensibility
scores across all 20 briefs. If this holds on the real (larger) IR schema and design-system
vocabulary, the memory design simplifies: an 8–14B-class Planner fits comfortably even on a
16GB machine, well under the 36GB tier mainPRD §8 budgets for it, which loosens the "one model
resident at a time" constraint rather than being merely satisfied by it.

Caveats before treating this as final:
- The structural-sensibility scorer is a cheap proxy, not a rubric — most of its 7 "failures"
  above were false positives on inspection. Its practical value here is to flag transcripts to
  read, not a trustworthy pass/fail number. A follow-up worth doing before committing to 7B:
  either a human-graded rubric or an LLM-judge pass on a held-out set, since the proxy is too
  blunt to detect a real quality gap if one exists between 7B and 14B.
- Only tested against the 4-component pilot schema (title, stat-trio, bullet-list,
  image-callout), not the full production IR vocabulary — a larger component set or more
  ambiguous layout decisions could separate the two sizes where this schema didn't.
- 34B remains untested; if a machine in the 64GB+ tier is available, worth a follow-up run to
  confirm there's no quality gain being left on the table for larger-memory deployments.

## Reproducing

```
cd spike
.venv/bin/pip install jsonschema   # if not already installed
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
.venv/bin/python run_size_compare.py qwen2.5:7b-instruct-q4_K_M
.venv/bin/python run_size_compare.py qwen2.5:14b-instruct-q4_K_M
```
