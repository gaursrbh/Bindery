#!/usr/bin/env python3
"""Spike: test the locally-installed `claude` CLI (headless mode) against bindery.pptx/v1.

Same prompted-JSON + manual-validation approach as run_claude.py, but invoked via
`claude --print` as a subprocess instead of the Messages API directly. All tools are
disallowed so this is a pure text-in/JSON-out call, not an agentic session.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.exit("pip install jsonschema")

HERE = Path(__file__).parent

env_file = HERE / ".env.local"
if env_file.exists() and "ANTHROPIC_API_KEY" not in os.environ:
    for line in env_file.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip()
SCHEMA = json.loads((HERE / "schema.json").read_text())
BRIEFS = json.loads((HERE / "briefs.json").read_text())

SYSTEM = f"""You are the Planner in a slide-generation pipeline. Given a brief, produce a single
Composition IR JSON object conforming to this bindery.pptx/v1 JSON Schema:

{json.dumps(SCHEMA, indent=2)}

Use ONLY the components defined in the schema. Never invent colors, coordinates, or font
sizes — "accent" is one of: primary, secondary, neutral. Output ONLY the JSON object,
nothing else — no markdown fences, no commentary."""


def build_prompt(brief):
    return f"Brief:\n{json.dumps(brief, indent=2)}\n\nProduce the Composition IR JSON now."


def call_cli(model, prompt):
    t0 = time.time()
    proc = subprocess.run(
        [
            "claude", "--print", "--bare",
            "--model", model,
            "--system-prompt", SYSTEM,
            "--disallowedTools", "*",
            "--output-format", "text",
            prompt,
        ],
        capture_output=True, text=True, timeout=180,
    )
    elapsed = time.time() - t0
    if proc.returncode != 0:
        raise RuntimeError(f"exit {proc.returncode}: {proc.stderr.strip()[:300]}")
    return proc.stdout, elapsed


def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def validate(raw):
    cleaned = strip_fences(raw)
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return False, f"invalid JSON: {e}"
    try:
        jsonschema.validate(obj, SCHEMA)
    except jsonschema.ValidationError as e:
        return False, f"schema violation: {e.message}"
    return True, None


def run(model):
    print(f"\n=== claude CLI (--print --bare), prompted JSON + manual validation ({model}) ===")
    results = []
    for brief in BRIEFS:
        prompt = build_prompt(brief)
        try:
            raw, elapsed = call_cli(model, prompt)
        except Exception as e:
            print(f"  {brief['id']:25s} ERROR calling CLI: {e}")
            results.append({"id": brief["id"], "ok": False, "error": str(e), "elapsed": None})
            continue
        ok, err = validate(raw)
        status = "PASS" if ok else "FAIL"
        print(f"  {brief['id']:25s} {status:5s} {elapsed:5.1f}s  {err or ''}")
        results.append({"id": brief["id"], "ok": ok, "error": err, "elapsed": elapsed, "raw": raw})
    n_ok = sum(r["ok"] for r in results)
    print(f"  -> {n_ok}/{len(results)} first-attempt valid")
    return results


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "claude-sonnet-5"
    results = run(model)
    out = HERE / f"results-cli-{model.replace('/', '_')}-prompted.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out}")
