def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _column(items, x, header, header_color, tokens):
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    parts = [
        f'<text x="{x}" y="0" font-size="{label_size + 4}" font-weight="bold" '
        f'fill="{header_color}">{_escape(header)}</text>'
    ]
    row_h = label_size + 12
    for i, item in enumerate(items):
        parts.append(
            f'<text x="{x}" y="{(i + 1) * row_h + 6}" font-size="{label_size}" '
            f'fill="{_color(tokens, "text")}">• {_escape(item)}</text>'
        )
    height = (len(items) + 1) * row_h
    return "".join(parts), height


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    half = width / 2
    left_svg, left_h = _column(
        props["left_items"], 0, props["left_label"], _color(tokens, "primary"), tokens
    )
    right_svg, right_h = _column(
        props["right_items"], half + 24, props["right_label"], _color(tokens, "secondary"), tokens
    )
    divider_h = max(left_h, right_h)
    divider = (
        f'<line x1="{half}" y1="0" x2="{half}" y2="{divider_h}" '
        f'stroke="{_color(tokens, "neutral")}" stroke-width="1"/>'
    )
    svg = f'<g transform="translate({x},{y + 14})">{left_svg}{right_svg}{divider}</g>'
    return svg, divider_h + 30
