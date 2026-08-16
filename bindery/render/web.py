"""(Composition, DesignSystem) -> single-file .html — mainPRD R5, M2-spec.md §2.

Per-DS isolated Vite project (design-systems/<name>/components/web/) builds a
temp entry embedding the composition + tokens as static data, via subprocess
`npm run build` (no network — dependencies are pre-installed by a one-time
`npm install`, run out of band, not by this renderer).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from bindery.ds.loader import SCHEMA_ROOT, DesignSystem
from bindery.ds.errors import DesignSystemError
from bindery.render.errors import CompositionError, WebBuildError

_CORE_SCHEMA = json.loads((SCHEMA_ROOT / "core.schema.json").read_text())
_REGISTRY = Registry().with_resource(
    "core.schema.json", Resource.from_contents(_CORE_SCHEMA)
)


@dataclass
class RenderResult:
    path: Path
    duration_ms: int
    blocks_rendered: int


def _validate(composition: dict, ds: DesignSystem) -> dict:
    target = composition.get("target")
    schema = ds.effective_schemas.get(target)
    if schema is None:
        raise CompositionError(
            f"design system '{ds.spec}' has no schema for target {target!r}; "
            f"available targets: {sorted(ds.effective_schemas)}"
        )

    schema_for_validation = {k: v for k, v in schema.items() if k != "$id"}
    validator = Draft202012Validator(schema_for_validation, registry=_REGISTRY)
    errors = sorted(validator.iter_errors(composition), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        location = "/".join(str(p) for p in first.path) or "<root>"
        available = sorted(_component_names(schema))
        raise CompositionError(
            f"composition invalid at {location}: {first.message}; "
            f"available components: {available}"
        )
    return schema


def _component_names(effective_schema: dict) -> list[str]:
    defs = effective_schema.get("$defs", {})
    names = []
    for def_schema in defs.values():
        const = def_schema.get("properties", {}).get("component", {}).get("const")
        if const:
            names.append(const)
    return names


def _tokens_css(tokens: dict) -> str:
    lines = [":root {"]
    for category, entries in tokens.items():
        if not isinstance(entries, dict):
            continue
        for name, spec in entries.items():
            value = spec.get("value") if isinstance(spec, dict) else spec
            if value is None:
                continue
            if category == "typography" and name.endswith("size") and str(value).isdigit():
                value = f"{value}px"
            lines.append(f"  --{category}-{name}: {value};")
    lines.append("}")
    return "\n".join(lines)


def _entry_source(component_names: list[str], composition: dict, tokens: dict) -> str:
    imports = []
    map_entries = []
    for name in component_names:
        var = "C_" + name.replace("-", "_")
        imports.append(f'import {var} from "./components/{name}.jsx";')
        map_entries.append(f'  "{name}": {var},')

    return (
        'import React from "react";\n'
        'import { createRoot } from "react-dom/client";\n'
        'import "./tokens.css";\n'
        + "\n".join(imports)
        + "\n\n"
        f"const tokens = {json.dumps(tokens)};\n"
        f"const blocks = {json.dumps(composition['blocks'])};\n"
        "const componentMap = {\n" + "\n".join(map_entries) + "\n};\n\n"
        "function App() {\n"
        "  return React.createElement(\n"
        '    "div",\n'
        '    { className: "bindery-page" },\n'
        "    blocks.map((b, i) => {\n"
        "      const C = componentMap[b.component];\n"
        "      return React.createElement(C, { key: i, props: b.props, tokens });\n"
        "    })\n"
        "  );\n"
        "}\n\n"
        'createRoot(document.getElementById("root")).render(React.createElement(App));\n'
    )


def render(composition: dict, ds: DesignSystem, out_path: Path) -> RenderResult:
    start = time.monotonic()
    schema = _validate(composition, ds)

    web_dir = ds.path / "components" / "web"
    node_modules = web_dir / "node_modules"
    if not node_modules.is_dir():
        raise DesignSystemError(
            str(node_modules.relative_to(ds.path)),
            "web",
            "not installed — run `npm install` in this directory before rendering",
        )

    entry_path = web_dir / "src" / ".bindery-entry.jsx"
    tokens_css_path = web_dir / "src" / "tokens.css"

    entry_path.write_text(
        _entry_source(_component_names(schema), composition, ds.tokens)
    )
    tokens_css_path.write_text(_tokens_css(ds.tokens))

    with tempfile.TemporaryDirectory() as tmp:
        try:
            proc = subprocess.run(
                ["npm", "run", "build", "--", "--outDir", tmp, "--emptyOutDir"],
                cwd=web_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
        finally:
            entry_path.unlink(missing_ok=True)
            tokens_css_path.unlink(missing_ok=True)

        if proc.returncode != 0:
            raise WebBuildError(proc.stderr or proc.stdout)

        built_html = list(Path(tmp).glob("*.html"))
        if not built_html:
            raise WebBuildError("build succeeded but produced no .html output")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(built_html[0], out_path)

    duration_ms = int((time.monotonic() - start) * 1000)
    return RenderResult(
        path=out_path, duration_ms=duration_ms, blocks_rendered=len(composition["blocks"])
    )
