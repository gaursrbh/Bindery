#!/usr/bin/env python3
"""Spike: Claude API with forced tool-use / input_schema (native structured-output enforcement).

The IR schema is passed as a tool's input_schema and tool_choice forces that tool, so the
API constrains the model's output at generation time — the like-for-like alternative to
Ollama's JSON-schema-enforced sampling mode.
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent

env_file = HERE / ".env.local"
if env_file.exists() and "ANTHROPIC_API_KEY" not in os.environ:
    for line in env_file.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip()

try:
    import jsonschema
    import anthropic
except ImportError:
    sys.exit("pip install jsonschema anthropic")

SCHEMA = json.loads((HERE / "schema.json").read_text())
BRIEFS = json.loads((HERE / "briefs.json").read_text())

# Tool input_schema must be a plain JSON Schema object (no top-level $schema/$id quirks needed,
# but Anthropic's tool schema is a subset — no $defs/$ref support in older API versions, so we
# inline defs manually here for safety).
TOOL_SCHEMA = json.loads(json.dumps(SCHEMA))  # keep $defs/$ref; API now supports draft 2020-12 subset incl. $ref

SYSTEM = """You are the Planner in a slide-generation pipeline. Given a brief, call the
emit_composition tool with a single Composition IR conforming to its schema. Use ONLY the
components defined in the schema. Never invent colors, coordinates, or font sizes —
"accent" is one of: primary, secondary, neutral."""


def build_prompt(brief):
    return f"Brief:\n{json.dumps(brief, indent=2)}\n\nCall emit_composition now."


def call_claude(client, model, prompt):
    t0 = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM,
        tools=[{
            "name": "emit_composition",
            "description": "Emit the Composition IR for the requested brief.",
            "input_schema": TOOL_SCHEMA,
        }],
        tool_choice={"type": "tool", "name": "emit_composition"},
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.time() - t0
    for block in resp.content:
        if block.type == "tool_use":
            return block.input, elapsed
    return None, elapsed


def validate(obj):
    if obj is None:
        return False, "no tool_use block returned"
    try:
        jsonschema.validate(obj, SCHEMA)
    except jsonschema.ValidationError as e:
        return False, f"schema violation: {e.message}"
    return True, None


def run(model):
    client = anthropic.Anthropic()
    print(f"\n=== Claude API, forced tool-use / input_schema ({model}) ===")
    results = []
    for brief in BRIEFS:
        prompt = build_prompt(brief)
        try:
            obj, elapsed = call_claude(client, model, prompt)
        except Exception as e:
            print(f"  {brief['id']:25s} ERROR calling model: {e}")
            results.append({"id": brief["id"], "ok": False, "error": str(e), "elapsed": None})
            continue
        ok, err = validate(obj)
        status = "PASS" if ok else "FAIL"
        print(f"  {brief['id']:25s} {status:5s} {elapsed:5.1f}s  {err or ''}")
        results.append({"id": brief["id"], "ok": ok, "error": err, "elapsed": elapsed, "raw": obj})
    n_ok = sum(r["ok"] for r in results)
    print(f"  -> {n_ok}/{len(results)} first-attempt valid")
    return results


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "claude-sonnet-5"
    results = run(model)
    out = HERE / f"results-{model.replace('/', '_')}-tooluse.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nWrote {out}")
