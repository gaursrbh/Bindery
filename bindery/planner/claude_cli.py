"""ClaudeCliPlanner — Claude Code CLI subprocess backend, billed against the
user's Pro/Max subscription (Claude Code's own OAuth session), not
per-token API billing. mainPRD §4 treats cloud inference as a non-goal for
privacy reasons; this is an explicit, opt-in escape hatch the user chose
knowingly (never a silent fallback when Ollama is slow/unavailable) — see
the CLI's `--planner claude-cli` flag.

The Messages-API-key-billed path (ClaudePlanner) is deliberately not built
yet — deferred, lower priority than this one per explicit instruction.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass

from bindery.ds.loader import DesignSystem
from bindery.planner.base import RepairContext
from bindery.planner.errors import PlannerError
from bindery.planner.prompts import build_system_prompt, build_user_prompt
from bindery.planner.schema_utils import flatten_effective_schema

_TIMEOUT_S = 180


@dataclass
class ClaudeCliConfig:
    model: str = "claude-haiku-4-5"
    binary: str = "claude"


class ClaudeCliPlanner:
    """Shells out to `claude -p --output-format json --json-schema ...`.

    Deliberately does NOT pass --bare: --bare forces API-key-only auth
    (OAuth/keychain never read, per `claude --help`) — the whole point of
    this backend is using the CLI's own subscription OAuth session. If the
    session isn't logged in, `claude` itself reports that in stderr/exit
    code and it surfaces here as a PlannerError, same as Ollama being down.
    """

    def __init__(self, config: ClaudeCliConfig | None = None):
        self.config = config or ClaudeCliConfig()

    def plan(
        self,
        brief: str,
        ds: DesignSystem,
        target: str,
        *,
        repair: RepairContext | None = None,
    ) -> dict:
        if shutil.which(self.config.binary) is None:
            raise PlannerError(f"'{self.config.binary}' CLI not found on PATH")

        schema = ds.effective_schemas.get(target)
        if schema is None:
            raise PlannerError(
                f"design system '{ds.spec}' has no schema for target {target!r}"
            )

        system = build_system_prompt(ds, target)
        user = build_user_prompt(brief, repair)
        flat_schema = flatten_effective_schema(schema)

        cmd = [
            self.config.binary,
            "-p",
            "--output-format", "json",
            "--model", self.config.model,
            "--system-prompt", system,
            "--json-schema", json.dumps(flat_schema),
            user,
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            raise PlannerError(f"'{self.config.binary}' timed out after {_TIMEOUT_S}s")
        except OSError as e:
            raise PlannerError(f"failed to run '{self.config.binary}': {e}")

        if proc.returncode != 0:
            raise PlannerError(
                f"'{self.config.binary}' exited {proc.returncode}: {proc.stderr.strip()}"
            )

        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            raise PlannerError(f"'{self.config.binary}' returned a non-JSON envelope: {e}")

        if envelope.get("is_error"):
            raise PlannerError(f"'{self.config.binary}' reported an error: {envelope.get('result')}")

        composition = envelope.get("structured_output")
        if composition is None:
            raise PlannerError(
                f"'{self.config.binary}' response had no structured_output "
                f"(stop_reason={envelope.get('stop_reason')!r})"
            )
        if not isinstance(composition.get("blocks"), list):
            raise PlannerError(
                "'structured_output.blocks' was not a JSON array — "
                "the --json-schema likely failed strict validation "
                "(check stderr for 'strict mode' warnings)"
            )
        return composition
