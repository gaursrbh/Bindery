"""bindery.lock — mainPRD §6.6, M3-spec.md §3."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_EXCLUDED_DIRS = {"node_modules"}
_EXCLUDED_FILES = {".bindery-entry.jsx", "tokens.css"}

RENDERER_VERSIONS = {"pptx": "pptx@0.1.0", "web": "web@0.1.0"}


def hash_design_system(ds_path: Path) -> str:
    """sha256 over sorted (relative_path, file_bytes) pairs under ds_path,
    excluding node_modules/ and renderer-generated files."""
    entries = []
    for p in sorted(ds_path.rglob("*")):
        if not p.is_file():
            continue
        if p.name in _EXCLUDED_FILES:
            continue
        if _EXCLUDED_DIRS & set(p.relative_to(ds_path).parts):
            continue
        entries.append(p)

    hasher = hashlib.sha256()
    for p in entries:
        rel = str(p.relative_to(ds_path))
        hasher.update(rel.encode())
        hasher.update(p.read_bytes())
    return f"sha256:{hasher.hexdigest()}"


@dataclass
class Lock:
    design_system: str
    design_system_hash: str
    renderer: str
    schema: str
    composition: dict
    models: dict = field(default_factory=dict)
    seed: int | None = None
    created: str = ""

    def to_dict(self) -> dict:
        return {
            "design_system": self.design_system,
            "design_system_hash": self.design_system_hash,
            "renderer": self.renderer,
            "models": self.models,
            "seed": self.seed,
            "schema": self.schema,
            "created": self.created,
            "composition": self.composition,
        }


def build_lock(
    ds_path: Path,
    ds_spec: str,
    target: str,
    composition: dict,
    models: dict | None = None,
    seed: int | None = None,
) -> Lock:
    return Lock(
        design_system=ds_spec,
        design_system_hash=hash_design_system(ds_path),
        renderer=RENDERER_VERSIONS[target],
        schema=composition["schema"],
        composition=composition,
        models=models or {},
        seed=seed,
        created=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def write_lock(lock: Lock, path: Path) -> None:
    path.write_text(json.dumps(lock.to_dict(), indent=2))


def read_lock(path: Path) -> Lock:
    data = json.loads(path.read_text())
    return Lock(**data)
