def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict) -> str:
    accent = f"var(--color-{props.get('accent', 'neutral')})"
    return (
        '<div class="bindery-image-callout">'
        f'<div style="font-size:var(--typography-stat-label-size);color:{accent};">'
        f"[{_esc(props['asset'])}]</div>"
        f'<div style="font-size:var(--typography-stat-label-size);color:var(--color-text);">'
        f"{_esc(props['caption'])}</div></div>"
    )
