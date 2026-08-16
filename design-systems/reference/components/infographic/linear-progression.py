def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    accent = _color(tokens, "primary")
    text_color = _color(tokens, "text")
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    row_h = 56
    radius = 14

    parts = [f'<g transform="translate({x},{y})">']
    steps = props["steps"]
    for i, step in enumerate(steps):
        cy = i * row_h + radius
        if i > 0:
            parts.append(
                f'<line x1="{radius}" y1="{cy - row_h + radius}" x2="{radius}" y2="{cy - radius}" '
                f'stroke="{accent}" stroke-width="2"/>'
            )
        parts.append(
            f'<circle cx="{radius}" cy="{cy}" r="{radius}" fill="{accent}"/>'
            f'<text x="{radius}" y="{cy + 5}" font-size="{label_size}" fill="white" '
            f'text-anchor="middle" font-weight="bold">{i + 1}</text>'
        )
        label_x = radius * 2 + 16
        parts.append(
            f'<text x="{label_x}" y="{cy - 2}" font-size="{label_size + 2}" '
            f'font-weight="bold" fill="{text_color}">{_escape(step["label"])}</text>'
        )
        if step.get("detail"):
            parts.append(
                f'<text x="{label_x}" y="{cy + label_size + 4}" font-size="{label_size}" '
                f'fill="{_color(tokens, "neutral")}">{_escape(step["detail"])}</text>'
            )
    parts.append("</g>")
    return "".join(parts), len(steps) * row_h + 16
