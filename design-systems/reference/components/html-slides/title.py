def _esc(text):
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def layout(props: dict, tokens: dict) -> str:
    accent = f"var(--color-{props.get('accent', 'primary')})"
    parts = ['<div class="bindery-title">']
    if props.get("eyebrow"):
        parts.append(
            f'<p style="margin:0 0 6px;font-weight:700;font-size:'
            f'var(--typography-eyebrow-size);color:{accent};">'
            f"{_esc(props['eyebrow'].upper())}</p>"
        )
    parts.append(
        f'<h1 style="margin:0;font-size:var(--typography-headline-size);'
        f'color:var(--color-text);">{_esc(props["headline"])}</h1>'
    )
    parts.append("</div>")
    return "".join(parts)
