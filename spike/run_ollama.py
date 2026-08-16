#!/usr/bin/env python3
"""Spike: test Ollama's JSON-schema-enforced sampling mode against the bindery.pptx/v1 IR.

For each brief, prompt the model to produce a Composition IR, constrained via
Ollama's `format: <json-schema>` request field, then validate the raw output
against the real schema. Scores first-attempt schema validity (no repair loop).
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.exit("pip install jsonschema")

HERE = Path(__file__).parent
SCHEMA = json.loads((HERE / "schema.json").read_text())
BRIEFS = json.loads((HERE / "briefs.json").read_text())
OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM = """You are the Planner in a slide-generation pipeline. Given a brief, produce a single
Composition IR JSON object conforming to the bindery.pptx/v1 schema. Use ONLY these components:
title, stat-trio, bullet-list, image-callout. Never invent colors, coordinates, or font sizes —
"accent" is one of: primary, secondary, neutral. Output ONLY the JSON object, nothing else."""


def build_prompt(brief):
    return (
        f"{SYSTEM}\n\nBrief:\n{json.dumps(brief, indent=2)}\n\n"
        f"Produce the Composition IR JSON now."
    )


def call_ollama(model, prompt, use_schema):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "seed": 42},
    }
    if use_schema:
        payload["format"] = SCHEMA
    else:
        payload["format"] = "json"
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read())
    elapsed = time.time() - t0
    return body.get("response", ""), elapsed


def validate(raw):
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, f"invalid JSON: {e}"
    try:
        jsonschema.validate(obj, SCHEMA)
    except jsonschema.ValidationError as e:
        return False, f"schema violation: {e.message}"
    return True, None


def run(model, use_schema, label):
    print(f"\n=== {label} ({model}) ===")
    results = []
    for brief in BRIEFS:
        prompt = build_prompt(brief)
        try:
            raw, elapsed = call_ollama(model, prompt, use_schema)
        except Exception as e:
            print(f"  {brief['id']:25s} ERROR calling model: {e}")
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
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:14b-instruct-q4_K_M"
    mode = sys.argv[2] if len(sys.argv) > 2 else "schema"  # schema | json | none
    label = {"schema": "JSON-schema-enforced", "json": "generic JSON mode", "none": "no constraint"}[mode]
    results = run(model, use_schema=(mode == "schema"), label=label)
    out = HERE / f"results-{model.replace(':', '_')}-{mode}.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out}")
