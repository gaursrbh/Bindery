# Structured-output enforcement spike — results

Answers issue #2 / mainPRD §12.1, §13. Schema and briefs in `schema.json` / `briefs.json`
(a representative `bindery.pptx/v1` IR schema with 4 components, and 6 briefs modeled on
§6.1's brief format). Scoring is first-attempt schema validity — no repair loop — since
the repair loop (§7 step 3) is a separate mitigation layered on top of whichever mechanism
is chosen here.

## What changed mid-spike

Original plan was to compare three local mechanisms (Ollama JSON-schema mode, llama.cpp
GBNF, Apple `@Generable`). Direction changed twice during the spike: first to "the project
may call the Claude API," then to "also test the locally-installed `claude` CLI as an access
path." The local GBNF and `@Generable` legs were dropped unrun in favor of the Claude legs,
since those are the more decision-relevant comparisons now. Final set tested: 4 mechanisms
across 2 access paths (API, CLI) x 2 enforcement modes (constrained, prompted-only).

## Results

| Mechanism | Access path | Enforcement | First-attempt valid | Avg latency |
|---|---|---|---|---|
| Ollama JSON-schema-enforced sampling (`format: <schema>`) | local model | hard (grammar-constrained decoding) | **6/6** | 23.6s |
| Claude, forced tool-use / `input_schema` | API | soft (trained tool-calling, not grammar) | **5/6** | 5.1s |
| Claude, headless CLI (`claude --print --bare`) | CLI subprocess | none (prompted JSON) | **5/6** | 4.9s |
| Claude, prompted JSON + manual validation | API | none (prompted JSON) | **4/6** | 4.1s |

Failure modes, all schema-mechanical, none a reasoning/content failure:
- **Prompted API** (`q3-board-update`): duplicate top-level `heading` key alongside `props`,
  violating `additionalProperties: false`.
- **Prompted API** (`incident-postmortem`): a stat label exceeded the 30-char `maxLength`.
- **CLI** (`incident-postmortem`): model added an extra `heading_note` key outside `props`.
- **Forced tool-use** (`risk-summary`): model wrapped the entire composition in an
  extra top-level `composition` key instead of emitting the schema fields directly as the
  tool's arguments — despite `tool_choice` forcing that exact tool and `input_schema` stating
  `additionalProperties: false` at the top level.

## Reading these results

- **The forced-tool-use failure is the important finding.** Anthropic's tool-use is *not*
  grammar-constrained decoding — `tool_choice` forces which tool is called, and the model is
  trained to fill `input_schema` accurately, but there is no token-level sampling mask like
  Ollama's `format: <schema>` or llama.cpp GBNF. A malformed call is a client-side error
  Anthropic's SDK does not silently repair; it can still violate `additionalProperties: false`.
  Structurally, this puts Claude's tool-use in the same category as Ollama's *generic*
  `"format": "json"` mode, not its schema-constrained mode — meaningfully better than
  free-text prompting (fewer degrees of freedom, a real schema anchor), but not the same hard
  guarantee "spike it and it structurally cannot fail" implies for GBNF/Ollama-schema.
- **CLI vs. direct API, same model, same failure category.** 5/6 (CLI) vs. 4/6 (API,
  prompted) is noise at n=6, not a systematic CLI penalty — same underlying model, same
  prompted-JSON weakness. The CLI adds ~0.5–1s of process/session overhead per call and a
  dependency on the `claude` binary's own versioning/auth (`--bare` requires
  `ANTHROPIC_API_KEY` directly; without it, it needs an interactive `/login` session), which is
  a worse fit for a headless server-side Planner role than calling the API directly — the CLI
  buys nothing here that the API doesn't already give you, and adds a subprocess + binary
  dependency.
- Only Ollama's schema mode delivered a structural, not statistical, guarantee across all 6
  cases here.

## Recommendation

**Only local grammar/schema-constrained decoding (Ollama's `format: <schema>`, or
equivalently llama.cpp GBNF, untested here but same mechanism) gives the hard guarantee
mainPRD §8 asks for** — "structured output is a hard requirement, not a prompt technique."
Claude's forced tool-use is a strong second (5/6, real schema anchoring, fast, zero local
setup) but is not that same guarantee — it failed on this schema even with `tool_choice`
forcing the call. The plain prompted-JSON paths (API or CLI) are the weakest of the four and
shouldn't be treated as the enforcement mechanism on their own, only as an option if the
repair loop is doing the real work.

If Claude API access is a durable option going forward, it's still attractive relative to
local models for latency (4–5s vs. 24s) and zero memory-budget/model-residency constraints
(§8) — but pair it with a repair loop (§7 step 3) rather than treating `tool_choice` alone
as sufficient enforcement, and don't add the CLI as a second access path: it has no
enforcement advantage over the API and adds a process/auth dependency for no benefit in a
non-interactive server role.

This is a product tradeoff, not just an engineering one: local constrained decoding keeps
the offline/reproducibility guarantee `bindery.lock` is built around (§6.6) at the cost of
~5x latency and local memory budgeting; the Claude API is faster and removes the memory
constraint but breaks offline operation and pins reproducibility to a hosted model version
Anthropic controls, not you.

**Fallback**, per §13, unchanged: if no mechanism proves reliable enough even with a repair
loop, fall back to a form-based brief that constructs the IR semi-manually.

## Reproducing

```
cd spike
python3 -m venv .venv && .venv/bin/pip install jsonschema anthropic
.venv/bin/python run_ollama.py qwen2.5:14b-instruct-q4_K_M schema   # requires: brew install ollama; ollama pull qwen2.5:14b-instruct-q4_K_M
.venv/bin/python run_claude.py claude-sonnet-5                       # requires: ANTHROPIC_API_KEY in spike/.env.local or env
.venv/bin/python run_claude_tooluse.py claude-sonnet-5                # forced tool-use / input_schema
.venv/bin/python run_claude_cli.py claude-sonnet-5                    # requires: claude CLI installed + ANTHROPIC_API_KEY
```
