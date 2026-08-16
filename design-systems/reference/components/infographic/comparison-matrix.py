def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    columns = props["columns"]
    rows = props["rows"]
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    row_h = label_size + 16
    label_col_w = 140
    col_w = (width - label_col_w) / len(columns)
    text_color = _color(tokens, "text")
    neutral = _color(tokens, "neutral")

    parts = [f'<g transform="translate({x},{y})">']
    for c, col in enumerate(columns):
        cx = label_col_w + c * col_w + col_w / 2
        parts.append(
            f'<text x="{cx}" y="0" font-size="{label_size}" font-weight="bold" '
            f'text-anchor="middle" fill="{text_color}">{_escape(col)}</text>'
        )
    parts.append(
        f'<line x1="0" y1="10" x2="{width}" y2="10" stroke="{neutral}" stroke-width="1"/>'
    )
    for r, row in enumerate(rows):
        ry = (r + 1) * row_h + 10
        parts.append(
            f'<text x="0" y="{ry}" font-size="{label_size}" font-weight="bold" '
            f'fill="{text_color}">{_escape(row["label"])}</text>'
        )
        for c, val in enumerate(row["values"]):
            cx = label_col_w + c * col_w + col_w / 2
            parts.append(
                f'<text x="{cx}" y="{ry}" font-size="{label_size}" text-anchor="middle" '
                f'fill="{neutral}">{_escape(val)}</text>'
            )
    parts.append("</g>")
    height = (len(rows) + 1) * row_h + 20
    return "".join(parts), height
