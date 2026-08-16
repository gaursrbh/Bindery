def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict) -> str:
    parts = ['<div class="bindery-bullet-list">']
    if props.get("heading"):
        parts.append(
            f'<div style="font-weight:700;font-size:var(--typography-stat-value-size);'
            f'color:var(--color-primary);margin-bottom:6px;">'
            f"{_esc(props['heading'])}</div>"
        )
    items = "".join(
        f'<li style="margin:4px 0;">{_esc(item)}</li>' for item in props["items"]
    )
    parts.append(
        f'<ul style="margin:0;padding-left:20px;font-size:var(--typography-stat-label-size);'
        f'color:var(--color-text);">{items}</ul></div>'
    )
    return "".join(parts)
