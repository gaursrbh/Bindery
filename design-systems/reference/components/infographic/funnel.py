def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> tuple[str, float]:
    stages = props["stages"]
    label_size = int(tokens["typography"]["stat-label-size"]["value"])
    accent = _color(tokens, "primary")
    n = len(stages)
    row_h = label_size + 30
    max_w = width * 0.8

    parts = [f'<g transform="translate({x},{y})">']
    for i, stage in enumerate(stages):
        top_w = max_w * (n - i) / n
        bottom_w = max_w * (n - i - 1) / n
        top_y = i * row_h
        bottom_y = top_y + row_h - 4
        top_l, top_r = (width - top_w) / 2, (width + top_w) / 2
        bot_l, bot_r = (width - bottom_w) / 2, (width + bottom_w) / 2
        opacity = 0.9 - 0.5 * i / max(n - 1, 1)
        parts.append(
            f'<polygon points="{top_l},{top_y} {top_r},{top_y} {bot_r},{bottom_y} {bot_l},{bottom_y}" '
            f'fill="{accent}" opacity="{opacity:.2f}"/>'
            f'<text x="{width / 2}" y="{(top_y + bottom_y) / 2 + 4}" font-size="{label_size}" '
            f'text-anchor="middle" fill="white" font-weight="bold">'
            f'{_escape(stage["label"])} — {_escape(stage["value"])}</text>'
        )
    parts.append("</g>")
    return "".join(parts), n * row_h + 10
