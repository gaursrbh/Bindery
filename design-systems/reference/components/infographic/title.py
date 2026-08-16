def _color(tokens, name):
    return tokens["color"][name]["value"]


def _escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def layout(props: dict, tokens: dict, x: float, y: float, width: float) -> str:
    accent = _color(tokens, props.get("accent", "primary"))
    text_color = _color(tokens, "text")
    headline_size = int(tokens["typography"]["headline-size"]["value"])
    eyebrow_size = int(tokens["typography"]["eyebrow-size"]["value"])

    parts = [f'<g transform="translate({x},{y})">']
    cursor_y = 0
    if props.get("eyebrow"):
        cursor_y += eyebrow_size
        parts.append(
            f'<text x="0" y="{cursor_y}" font-size="{eyebrow_size}" '
            f'font-weight="bold" fill="{accent}">{_escape(props["eyebrow"].upper())}</text>'
        )
        cursor_y += 8
    cursor_y += headline_size
    parts.append(
        f'<text x="0" y="{cursor_y}" font-size="{headline_size}" '
        f'font-weight="bold" fill="{text_color}">{_escape(props["headline"])}</text>'
    )
    parts.append("</g>")
    return "\n".join(parts), cursor_y + 16
