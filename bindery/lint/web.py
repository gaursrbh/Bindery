"""Web (HTML) token-compliance linting — M3-spec.md §2.3.

This is a client-rendered SPA (React mounts at runtime, no server-side
render) — the static .html has no baked-in DOM to inspect, and a naive
whole-file regex scan hits false positives from our own architecture: the
composition/tokens data embedded as JS literals for the runtime to consume,
and literal delta/label text content (e.g. "+1.4pt"). Discovered empirically
while implementing — scan is narrowed to `style:{...}` object literals only
(where our component code actually applies color/size), not the whole bundle.
"""

from __future__ import annotations

import re
from pathlib import Path

from bindery.ds.loader import DesignSystem

_STYLE_OBJ_RE = re.compile(r"style:\s*\{([^{}]*)\}")
_COLOR_PROP_RE = re.compile(r'\b\w*[cC]olor:\s*"([^"]*)"')
_SIZE_PROP_RE = re.compile(r'\b\w*[sS]ize:\s*"([^"]*)"')
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{3,6}$")
_PX_PT_RE = re.compile(r"^\d+(?:\.\d+)?(?:px|pt)$")
_VAR_RE = re.compile(r"^var\(--")


def lint(artifact_path: Path, ds: DesignSystem) -> list:
    from bindery.lint import LintViolation

    html = artifact_path.read_text()
    violations = []

    for m in _STYLE_OBJ_RE.finditer(html):
        line_no = html.count("\n", 0, m.start()) + 1
        style_body = m.group(1)

        for cm in _COLOR_PROP_RE.finditer(style_body):
            value = cm.group(1)
            if _HEX_RE.match(value) and not _VAR_RE.match(value):
                violations.append(LintViolation(f"line {line_no}", "color", value))

        for sm in _SIZE_PROP_RE.finditer(style_body):
            value = sm.group(1)
            if _PX_PT_RE.match(value) and not _VAR_RE.match(value):
                violations.append(LintViolation(f"line {line_no}", "font-size", value))

    return violations
