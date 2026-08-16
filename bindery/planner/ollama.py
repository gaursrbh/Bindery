"""OllamaPlanner — M1-spec.md §2.2."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from bindery.ds.loader import SCHEMA_ROOT, DesignSystem
from bindery.planner.base import RepairContext
from bindery.planner.components import describe_components
from bindery.planner.errors import PlannerError

_TIMEOUT_S = 180


def _flatten_for_ollama(effective_schema: dict) -> dict:
    """Ollama's `format:` schema compiler cannot resolve the external
    `$ref: "core.schema.json"` M0's effective schemas carry (allOf[0]) — it
    only follows local `#/$defs/...` refs, which is why the M0-spec's target
    vocab files use $refs for components but the shared envelope uses an
    external filename ref. Inline that one external ref; leave local $defs
    refs (blocks.items.oneOf) untouched, since those work fine (confirmed by
    issue #2/#3's spikes using an equivalent flat schema)."""
    with open(SCHEMA_ROOT / "core.schema.json") as f:
        core = json.load(f)

    core_branch, target_branch = effective_schema["allOf"]
    assert "$ref" in core_branch  # sanity: M0-spec.md §2's fixed allOf[0] shape

    return {
        "type": "object",
        "additionalProperties": False,
        "required": core["required"],
        "properties": {**core["properties"], **target_branch.get("properties", {})},
        "$defs": effective_schema.get("$defs", {}),
    }


@dataclass
class PlannerConfig:
    model: str = "qwen2.5:7b-instruct-q4_K_M"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    seed: int = 42


def _build_system_prompt(ds: DesignSystem, target: str) -> str:
    components = describe_components(ds, target)
    lines = [
        "You are the Planner in a slide-generation pipeline. Given a brief, "
        "produce a single Composition IR JSON object.",
        f'Set "schema" to "bindery/v1", "design_system" to "{ds.spec}", '
        f'"target" to "{target}".',
        "Use ONLY these components:",
    ]
    for c in components:
        lines.append(f"- {c.name}: {c.description}")
    lines.append(
        "Never invent props, colors, coordinates, or font sizes not present "
        "in the schema. Output ONLY the JSON object, nothing else."
    )
    return "\n".join(lines)


def _build_user_prompt(brief: str, repair: RepairContext | None) -> str:
    if repair is None:
        return f"Brief:\n{brief}\n\nProduce the Composition IR JSON now."
    return (
        f"Brief:\n{brief}\n\n"
        f"Your previous Composition IR failed to render:\n{repair.error}\n\n"
        f"Previous output:\n{json.dumps(repair.prior_composition)}\n\n"
        "Revise ONLY the text in the offending block/prop named above so it "
        "fits the available space (state a numeric target size to yourself and "
        "shorten to fit it). Keep every other block and prop byte-identical. "
        "Output ONLY the corrected Composition IR JSON object."
    )


class OllamaPlanner:
    def __init__(self, config: PlannerConfig | None = None):
        self.config = config or PlannerConfig()

    def plan(
        self,
        brief: str,
        ds: DesignSystem,
        target: str,
        *,
        repair: RepairContext | None = None,
    ) -> dict:
        schema = ds.effective_schemas.get(target)
        if schema is None:
            raise PlannerError(
                f"design system '{ds.spec}' has no schema for target {target!r}"
            )

        system = _build_system_prompt(ds, target)
        user = _build_user_prompt(brief, repair)
        prompt = f"{system}\n\n{user}"

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "format": _flatten_for_ollama(schema),
            "options": {
                "temperature": self.config.temperature,
                "seed": self.config.seed,
            },
        }
        req = urllib.request.Request(
            f"{self.config.base_url}/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
                body = json.loads(resp.read())
        except urllib.error.URLError as e:
            raise PlannerError(f"could not reach Ollama at {self.config.base_url}: {e}")
        except json.JSONDecodeError as e:
            raise PlannerError(f"Ollama returned a non-JSON response envelope: {e}")

        raw = body.get("response", "")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise PlannerError(f"model response was not valid JSON: {e}")
