"""Artifact library — mainPRD R9, M3-spec.md §4. Filesystem JSON index, not
SQLite (no GUI yet to justify a real query layer, issue #26)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

INDEX_FILENAME = ".bindery-index.json"


@dataclass
class ArtifactEntry:
    id: str
    path: str
    lock_path: str
    target: str
    design_system: str
    created: str


def _index_path(out_dir: Path) -> Path:
    return out_dir / INDEX_FILENAME


def _make_id(path: str, created: str) -> str:
    return hashlib.sha256(f"{path}:{created}".encode()).hexdigest()[:8]


def load_index(out_dir: Path) -> list[ArtifactEntry]:
    p = _index_path(out_dir)
    if not p.exists():
        return []
    return [ArtifactEntry(**e) for e in json.loads(p.read_text())]


def append_entry(
    out_dir: Path, artifact_path: Path, lock_path: Path, target: str, design_system: str, created: str
) -> ArtifactEntry:
    entry = ArtifactEntry(
        id=_make_id(artifact_path.name, created),
        path=artifact_path.name,
        lock_path=lock_path.name,
        target=target,
        design_system=design_system,
        created=created,
    )
    entries = load_index(out_dir)
    entries.append(entry)
    _index_path(out_dir).write_text(json.dumps([asdict(e) for e in entries], indent=2))
    return entry


def find_entry(out_dir: Path, artifact_id: str) -> ArtifactEntry | None:
    for e in load_index(out_dir):
        if e.id == artifact_id:
            return e
    return None
