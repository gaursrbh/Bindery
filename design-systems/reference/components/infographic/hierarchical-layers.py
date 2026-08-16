def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    layers = props["layers"]
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    row_h = label_size + 24
    n = len(layers)
    accent = _color(tokens, "primary")

    parts = [f'<g transform="translate({x},{y})">']
    for i, layer in enumerate(layers):
        # Narrowest at top, full width at the bottom.
        layer_w = width * (i + 1) / n
        lx = (width - layer_w) / 2
        ly = i * row_h
        opacity = 0.4 + 0.6 * (i + 1) / n
        parts.append(
            f'<rect x="{lx}" y="{ly}" width="{layer_w}" height="{row_h - 6}" '
            f'fill="{accent}" opacity="{opacity:.2f}"/>'
            f'<text x="{width / 2}" y="{ly + row_h / 2}" font-size="{label_size}" '
            f'text-anchor="middle" dominant-baseline="middle" fill="white" '
            f'font-weight="bold">{_escape(layer["label"])}</text>'
        )
    parts.append("</g>")
    return "".join(parts), n * row_h + 10
