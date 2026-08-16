import math


def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    stages = props["stages"]
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    accent = _color(tokens, "primary")
    neutral = _color(tokens, "neutral")

    radius = min(width, 400) / 2 - 50
    cx, cy = width / 2, radius + 50
    height = radius * 2 + 100
    n = len(stages)

    parts = [f'<g transform="translate({x},{y})">']
    points = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    for i in range(n):
        sx, sy = points[i]
        ex, ey = points[(i + 1) % n]
        parts.append(f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="{neutral}" stroke-width="1.5"/>')

    for i, stage in enumerate(stages):
        sx, sy = points[i]
        angle = 2 * math.pi * i / n - math.pi / 2
        anchor = "start" if math.cos(angle) > 0.15 else ("end" if math.cos(angle) < -0.15 else "middle")
        label_x = sx + (14 if anchor == "start" else (-14 if anchor == "end" else 0))
        parts.append(
            f'<circle cx="{sx}" cy="{sy}" r="10" fill="{accent}"/>'
            f'<text x="{label_x}" y="{sy + 4}" font-size="{label_size}" text-anchor="{anchor}" '
            f'fill="{_color(tokens, "text")}">{_escape(stage)}</text>'
        )
    parts.append("</g>")
    return "".join(parts), height
