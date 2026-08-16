import math


def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    spokes = props["spokes"]
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    accent = _color(tokens, "primary")
    secondary = _color(tokens, "secondary")
    neutral = _color(tokens, "neutral")

    radius = min(width, 400) / 2 - 60
    cx, cy = width / 2, radius + 60
    height = radius * 2 + 120

    parts = [f'<g transform="translate({x},{y})">']
    n = len(spokes)
    for i, spoke in enumerate(spokes):
        angle = 2 * math.pi * i / n - math.pi / 2
        sx = cx + radius * math.cos(angle)
        sy = cy + radius * math.sin(angle)
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{sx}" y2="{sy}" stroke="{neutral}" stroke-width="1.5"/>'
            f'<circle cx="{sx}" cy="{sy}" r="8" fill="{secondary}"/>'
        )
        anchor = "start" if math.cos(angle) > 0.15 else ("end" if math.cos(angle) < -0.15 else "middle")
        label_x = sx + (14 if anchor == "start" else (-14 if anchor == "end" else 0))
        parts.append(
            f'<text x="{label_x}" y="{sy + 4}" font-size="{label_size}" text-anchor="{anchor}" '
            f'fill="{_color(tokens, "text")}">{_escape(spoke)}</text>'
        )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="40" fill="{accent}"/>'
        f'<text x="{cx}" y="{cy + 5}" font-size="{label_size}" text-anchor="middle" '
        f'fill="white" font-weight="bold">{_escape(props["hub"])}</text>'
    )
    parts.append("</g>")
    return "".join(parts), height
