def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    primary = _color(tokens, "primary")
    secondary = _color(tokens, "secondary")
    text_color = _color(tokens, "text")

    radius = min(width, 400) / 4.2
    cy = radius + 30
    left_cx = width / 2 - radius * 0.6
    right_cx = width / 2 + radius * 0.6
    height = radius * 2 + 70

    parts = [
        f'<g transform="translate({x},{y})">'
        f'<circle cx="{left_cx}" cy="{cy}" r="{radius}" fill="{primary}" opacity="0.55"/>'
        f'<circle cx="{right_cx}" cy="{cy}" r="{radius}" fill="{secondary}" opacity="0.55"/>'
        f'<text x="{left_cx - radius * 0.5}" y="{cy}" font-size="{label_size}" '
        f'text-anchor="middle" fill="{text_color}">{_escape(props["left_label"])}</text>'
        f'<text x="{right_cx + radius * 0.5}" y="{cy}" font-size="{label_size}" '
        f'text-anchor="middle" fill="{text_color}">{_escape(props["right_label"])}</text>'
    ]
    if props.get("overlap_label"):
        parts.append(
            f'<text x="{width / 2}" y="{cy}" font-size="{label_size}" text-anchor="middle" '
            f'fill="white" font-weight="bold">{_escape(props["overlap_label"])}</text>'
        )
    parts.append("</g>")
    return "".join(parts), height
