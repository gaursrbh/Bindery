"""DS importer, PPTX input path only — mainPRD R13, M4-spec.md §4.

Extracts a *candidate* tokens.json for human review. Never installs a live
design system — components and rules still need human authoring; this is
token intake, not authoring (M4-spec.md §4.2).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from pptx import Presentation


@dataclass
class ImportReport:
    colors: Counter = field(default_factory=Counter)
    sizes: Counter = field(default_factory=Counter)
    fonts: Counter = field(default_factory=Counter)


def scan_pptx(path: Path) -> ImportReport:
    report = ImportReport()
    prs = Presentation(path)

    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for paragraph in shape.text_frame.paragraphs:
                fonts_to_check = [paragraph.font] + [r.font for r in paragraph.runs]
                for font in fonts_to_check:
                    if font.color and font.color.type is not None:
                        try:
                            report.colors[f"#{font.color.rgb}"] += 1
                        except (AttributeError, TypeError):
                            pass
                    if font.size is not None:
                        report.sizes[int(font.size.pt)] += 1
                    if font.name is not None:
                        report.fonts[font.name] += 1

    return report


def candidate_tokens(report: ImportReport) -> dict:
    ranked_colors = [c for c, _ in report.colors.most_common()]
    ranked_sizes = sorted(report.sizes.most_common(), key=lambda kv: -kv[1])
    top_font = report.fonts.most_common(1)[0][0] if report.fonts else "Helvetica Neue"

    color_slots = ["primary", "secondary", "neutral", "background", "text"]
    color_tokens = {
        slot: {"value": ranked_colors[i]}
        for i, slot in enumerate(color_slots)
        if i < len(ranked_colors)
    }

    size_names = ["headline-size", "stat-value-size", "eyebrow-size", "stat-label-size"]
    typography_tokens = {"family": {"value": top_font}}
    for i, name in enumerate(size_names):
        if i < len(ranked_sizes):
            typography_tokens[name] = {"value": str(ranked_sizes[i][0])}

    return {"color": color_tokens, "typography": typography_tokens}


def write_candidate(deck_path: Path, out_dir: Path) -> Path:
    report = scan_pptx(deck_path)
    tokens = candidate_tokens(report)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidate-tokens.json"
    out_path.write_text(json.dumps(tokens, indent=2))
    return out_path
