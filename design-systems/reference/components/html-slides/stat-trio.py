def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def layout(props: dict, tokens: dict) -> str:
    cols = []
    for stat in props["stats"]:
        delta = (
            f'<div style="font-size:var(--typography-stat-label-size);'
            f'color:var(--color-secondary);">{_esc(stat["delta"])}</div>'
            if "delta" in stat
            else ""
        )
        cols.append(
            '<div style="flex:1;">'
            f'<div style="font-weight:700;font-size:var(--typography-stat-value-size);'
            f'color:var(--color-primary);">{_esc(stat["value"])}</div>'
            f'<div style="font-size:var(--typography-stat-label-size);'
            f'color:var(--color-neutral);">{_esc(stat["label"])}</div>'
            f"{delta}</div>"
        )
    return f'<div style="display:flex;gap:24px;">{"".join(cols)}</div>'
