"""html-slides token-compliance linting.

Unlike the "web" target (a client-rendered React SPA whose static HTML has
no baked-in DOM — see bindery/lint/web.py), html-slides is server-rendered
plain HTML with real inline `style="..."` attributes, so a much simpler
regex — scanning attribute syntax, not JS object-literal syntax — actually
inspects real content here. Reusing web.py's linter directly would be a
silent false negative (its regex only matches `style:{...}`, which never
appears in this target's output), not a real check.
"""

from __future__ import annotations

import re
from pathlib import Path

from bindery.ds.loader import DesignSystem

_STYLE_ATTR_RE = re.compile(r'style="([^"]*)"')
_COLOR_PROP_RE = re.compile(r"\b\w*[cC]olor\s*:\s*([^;]+);?")
_SIZE_PROP_RE = re.compile(r"\bfont-size\s*:\s*([^;]+);?")
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{3,6}$")
_PX_PT_RE = re.compile(r"^\d+(?:\.\d+)?(?:px|pt)$")
_VAR_RE = re.compile(r"^var\(--")


def lint(artifact_path: Path, ds: DesignSystem) -> list:
    from bindery.lint import LintViolation

    html = artifact_path.read_text()
    violations = []

    for m in _STYLE_ATTR_RE.finditer(html):
        line_no = html.count("\n", 0, m.start()) + 1
        style_body = m.group(1)

        for cm in _COLOR_PROP_RE.finditer(style_body):
            value = cm.group(1).strip()
            if _HEX_RE.match(value) and not _VAR_RE.match(value):
                violations.append(LintViolation(f"line {line_no}", "color", value))

        for sm in _SIZE_PROP_RE.finditer(style_body):
            value = sm.group(1).strip()
            if _PX_PT_RE.match(value) and not _VAR_RE.match(value):
                violations.append(LintViolation(f"line {line_no}", "font-size", value))

    return violations
