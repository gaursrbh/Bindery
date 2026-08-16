"""diagram-design subprocess adapter — issues #52-56.

Bridges Bindery's tokens.json to cathrynlavery/diagram-design's `claude -p`
skill invocation. This is deliberately OUTSIDE render()'s purity boundary
(mainPRD §6.4): it shells out to a live, non-deterministic LLM subprocess,
the same way ClaudeCliPlanner does, and produces a resolved SVG asset file
on disk *before* the composition is built — render() itself only ever reads
that already-generated file, exactly as it reads any other static asset.

Vendors only the two skill files a given call actually needs (SKILL.md +
the one references/type-<type>.md) rather than requiring the user to
install the plugin globally, so this works from a fresh checkout.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

_REPO = "cathrynlavery/diagram-design"
_SKILL_PATH = "skills/diagram-design"
_CACHE_DIR = Path(".diagram-design-cache")

# issue #54 — Bindery token -> diagram-design semantic-role mapping. Bindery
# has no tint/shade computation, so paper-2/soft/accent-tint reuse the
# nearest flat token rather than a computed lighter variant; a real gap, not
# a silent one (documented in issue #54's resolution).
_ROLE_MAP = {
    "paper": ("color", "background"),
    "paper-2": ("color", "background"),
    "ink": ("color", "text"),
    "muted": ("color", "neutral"),
    "soft": ("color", "neutral"),
    "rule": ("color", "neutral"),
    "rule-solid": ("color", "text"),
    "accent": ("color", "secondary"),
    "accent-tint": ("color", "secondary"),
    "link": ("color", "primary"),
}


class DiagramDesignError(RuntimeError):
    pass


def style_guide_from_tokens(tokens: dict) -> str:
    """issue #54 — render a diagram-design references/style-guide.md
    fragment from a Bindery tokens.json, so the diagram-design agent skins
    its output to match the design system generating the surrounding deck."""
    lines = ["# Style guide (generated from Bindery design-system tokens)", ""]
    for role, (section, key) in _ROLE_MAP.items():
        value = tokens.get(section, {}).get(key, {}).get("value")
        if value:
            lines.append(f"- `{role}`: {value}")
    family = tokens.get("typography", {}).get("family", {}).get("value")
    if family:
        lines.append(f"- font family: {family}")
    lines.append("")
    lines.append(
        "This style guide is already customized for the current project — "
        "skip the first-time-setup onboarding gate and proceed directly."
    )
    return "\n".join(lines)


def _fetch_skill_file(rel_path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    result = subprocess.run(
        ["gh", "api", f"repos/{_REPO}/contents/{_SKILL_PATH}/{rel_path}", "--jq", ".content"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise DiagramDesignError(f"could not fetch {rel_path} from {_REPO}: {result.stderr}")
    import base64
    dest.write_bytes(base64.b64decode(result.stdout.strip()))


# issue #55 — the 27 diagram-design visual types map 1:1 to their
# references/type-<slug>.md filenames.
KNOWN_TYPES = {
    "architecture", "it-state", "flowchart", "sequence", "state", "er",
    "timeline", "swimlane", "quadrant", "radar", "loop", "nested", "tree",
    "org-chart", "layers", "venn", "pyramid", "bar", "line", "gantt",
    "scatter", "high-level", "process", "medallion", "data-flow",
    "dp-integration", "dp-security-matrix",
}


@dataclass
class DiagramResult:
    svg_path: Path
    html_path: Path
    png_path: Path


def generate_diagram(
    diagram_type: str, description: str, tokens: dict, out_dir: Path,
    timeout: int = 180,
) -> DiagramResult:
    """issue #56 — runs before render(), never inside it. Fetches the
    minimal skill context, invokes `claude -p` non-interactively with
    file-write access scoped to a work directory, and returns the path to
    the self-contained HTML/SVG the agent produced."""
    if diagram_type not in KNOWN_TYPES:
        raise DiagramDesignError(f"unknown diagram type {diagram_type!r}; expected one of {sorted(KNOWN_TYPES)}")

    _CACHE_DIR.mkdir(exist_ok=True)
    _fetch_skill_file("SKILL.md", _CACHE_DIR / "SKILL.md")
    _fetch_skill_file(f"references/type-{diagram_type}.md", _CACHE_DIR / "references" / f"type-{diagram_type}.md")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "SKILL.md").write_text((_CACHE_DIR / "SKILL.md").read_text())
        (work / "references").mkdir()
        (work / "references" / f"type-{diagram_type}.md").write_text(
            (_CACHE_DIR / "references" / f"type-{diagram_type}.md").read_text()
        )
        (work / "style-guide.md").write_text(style_guide_from_tokens(tokens))

        prompt = (
            f"Read ./SKILL.md and ./references/type-{diagram_type}.md, then read "
            f"./style-guide.md and use it as the customized style guide (skip the "
            f"onboarding gate — it is already customized). Draw a '{diagram_type}' "
            f"diagram for: {description}. Write the final self-contained HTML/SVG "
            f"to ./diagram.html. Do not ask questions; proceed with reasonable "
            f"assumptions and note them in an HTML comment at the end of the file."
        )
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json", "--allowedTools", "Read,Write"],
            cwd=work, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            raise DiagramDesignError(f"claude -p failed: {result.stderr or result.stdout}")

        html_out = work / "diagram.html"
        if not html_out.exists():
            raise DiagramDesignError("claude -p completed but did not write diagram.html")
        html = html_out.read_text()

        match = re.search(r"<svg[\s\S]*?</svg>", html)
        if not match:
            raise DiagramDesignError("diagram.html did not contain an <svg> element")

        out_dir.mkdir(parents=True, exist_ok=True)
        svg_path = out_dir / "diagram.svg"
        svg_path.write_text(match.group())
        html_path = out_dir / "diagram.html"
        html_path.write_text(html)

        # issue #56 — rasterize so pptx (which embeds PNG/JPEG, not live
        # SVG) can pick it up via slide.shapes.add_picture, the same
        # cairosvg path the infographic renderer already uses.
        import cairosvg

        png_path = out_dir / "diagram.png"
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=2)

        return DiagramResult(svg_path=svg_path, html_path=html_path, png_path=png_path)
