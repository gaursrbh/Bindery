"""OllamaPlanner — M1-spec.md §2.2."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from bindery.ds.loader import DesignSystem
from bindery.planner.base import RepairContext
from bindery.planner.errors import PlannerError
from bindery.planner.prompts import build_system_prompt, build_user_prompt
from bindery.planner.schema_utils import flatten_effective_schema

_TIMEOUT_S = 180


@dataclass
class PlannerConfig:
    model: str = "qwen2.5:7b-instruct-q4_K_M"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    seed: int = 42


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

        system = build_system_prompt(ds, target)
        user = build_user_prompt(brief, repair)
        prompt = f"{system}\n\n{user}"

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "format": flatten_effective_schema(schema),
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
