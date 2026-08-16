#!/usr/bin/env python3
"""Spike: compare Planner model sizes (7B vs 14B, Ollama JSON-schema-enforced sampling)
against 20 representative briefs.

Answers issue #3 / mainPRD §12.2. Enforcement mechanism fixed per issue #2's recommendation
(Ollama `format: <schema>`, the only mechanism that gave a structural, not statistical,
guarantee in that spike). Scores two axes per brief:

1. First-attempt schema validity (same check as issue #2's spike).
2. Structural sensibility: does the IR actually reflect the brief? Cheap deterministic
   proxies, not a full rubric -- each is a necessary-not-sufficient signal:
   - every `must_include` keyword constraint appears (case-insensitive substring) somewhere
     in the emitted prop values
   - stat-trio is used only when the brief's sources contain numeric/stat-like content
   - block count is non-trivial (>=2) for briefs with more than one source fact
   - no placeholder/empty prop values (e.g. "TBD", "", "N/A")
"""
import json
import re
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
title, stat-trio, bullet-list, image-callout. Never invent colors, coordinates, or font sizes --
"accent" is one of: primary, secondary, neutral. Output ONLY the JSON object, nothing else."""

PLACEHOLDER_RE = re.compile(r"^\s*(tbd|n/?a|todo|xxx|placeholder|\.\.\.)\s*$", re.I)


def build_prompt(brief):
    return (
        f"{SYSTEM}\n\nBrief:\n{json.dumps(brief, indent=2)}\n\n"
        f"Produce the Composition IR JSON now."
    )


def call_ollama(model, prompt):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": SCHEMA,
        "options": {"temperature": 0.2, "seed": 42},
    }
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read())
    elapsed = time.time() - t0
    return body.get("response", ""), elapsed


def all_prop_strings(obj):
    out = []
    for block in obj.get("blocks", []):
        props = block.get("props", {})
        for v in props.values():
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        out.append(item)
                    elif isinstance(item, dict):
                        out.extend(str(x) for x in item.values() if isinstance(x, (str, int, float)))
    return out


def has_numeric_content(brief):
    return bool(re.search(r"\d", " ".join(brief.get("sources", []))))


def score_sensibility(brief, obj):
    notes = []
    ok = True

    strings = all_prop_strings(obj)
    haystack = " ".join(strings).lower()
    for kw in brief.get("constraints", {}).get("must_include", []):
        if kw.lower() not in haystack:
            ok = False
            notes.append(f"missing must_include: {kw!r}")

    components = [b.get("component") for b in obj.get("blocks", [])]
    if "stat-trio" in components and not has_numeric_content(brief):
        ok = False
        notes.append("stat-trio used but brief has no numeric source content")

    n_facts = len(brief.get("sources", [])) + len(brief.get("constraints", {}).get("must_include", []))
    if n_facts >= 2 and len(obj.get("blocks", [])) < 2:
        ok = False
        notes.append("brief has multiple facts but IR emitted <2 blocks")

    for s in strings:
        if PLACEHOLDER_RE.match(s):
            ok = False
            notes.append(f"placeholder value: {s!r}")

    return ok, notes


def validate_schema(raw):
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, None, f"invalid JSON: {e}"
    try:
        jsonschema.validate(obj, SCHEMA)
    except jsonschema.ValidationError as e:
        return False, obj, f"schema violation: {e.message}"
    return True, obj, None


def run(model):
    print(f"\n=== {model} ===")
    results = []
    for brief in BRIEFS:
        prompt = build_prompt(brief)
        try:
            raw, elapsed = call_ollama(model, prompt)
        except Exception as e:
            print(f"  {brief['id']:30s} ERROR calling model: {e}")
            results.append({"id": brief["id"], "schema_valid": False, "sensible": False,
                             "error": str(e), "elapsed": None})
            continue
        schema_valid, obj, err = validate_schema(raw)
        sensible, notes = (False, ["schema invalid, not scored"]) if not schema_valid else score_sensibility(brief, obj)
        status = f"{'S' if schema_valid else '-'}{'C' if sensible else '-'}"
        print(f"  {brief['id']:30s} {status}  {elapsed:5.1f}s  {err or '; '.join(notes)}")
        results.append({
            "id": brief["id"], "schema_valid": schema_valid, "sensible": sensible,
            "error": err, "notes": notes, "elapsed": elapsed, "raw": raw,
        })
    n_valid = sum(r["schema_valid"] for r in results)
    n_sensible = sum(r["sensible"] for r in results)
    avg_latency = sum(r["elapsed"] for r in results if r.get("elapsed")) / max(
        1, sum(1 for r in results if r.get("elapsed"))
    )
    print(f"  -> {n_valid}/{len(results)} schema-valid, {n_sensible}/{len(results)} structurally sensible, "
          f"avg {avg_latency:.1f}s")
    return results


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:14b-instruct-q4_K_M"
    results = run(model)
    out = HERE / f"results-size-{model.replace(':', '_')}.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out}")
