"""Target dispatch — M2-spec.md extends M0's pptx-only renderer with web."""

from __future__ import annotations

from pathlib import Path

from bindery.ds.loader import DesignSystem
from bindery.render import pptx as _pptx
from bindery.render import web as _web

_EXTENSIONS = {"pptx": "pptx", "web": "html"}

_RENDERERS = {"pptx": _pptx.render, "web": _web.render}


def extension_for(target: str) -> str:
    return _EXTENSIONS[target]


def render(composition: dict, ds: DesignSystem, out_path: Path):
    target = composition.get("target")
    renderer = _RENDERERS.get(target)
    if renderer is None:
        from bindery.render.errors import CompositionError

        raise CompositionError(
            f"no renderer for target {target!r}; available: {sorted(_RENDERERS)}"
        )
    return renderer(composition, ds, out_path)
