def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    accent = _color(tokens, props.get("accent", "primary"))
    label_color = _color(tokens, "neutral")
    value_size = int(tokens["typography"]["stat-value-size"]["value"])
    label_size = int(tokens["typography"]["stat-label-size"]["value"])

    value_y = value_size
    label_y = value_y + label_size + 6

    svg = (
        f'<g transform="translate({x},{y})">'
        f'<text x="0" y="{value_y}" font-size="{value_size}" font-weight="bold" '
        f'fill="{accent}">{_escape(props["value"])}</text>'
        f'<text x="0" y="{label_y}" font-size="{label_size}" '
        f'fill="{label_color}">{_escape(props["label"])}</text>'
        "</g>"
    )
    return svg, label_y + 16
