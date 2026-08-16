"""(Composition, tokens.json) -> single-file .html, per mainPRD §6.4 / R5.

Reads the exact same block/prop shape the pptx renderer reads for title and
stat-trio — the point of this spike is to prove those props don't need to
change between renderers, only the layout code consuming them.
"""
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def render_title(props, tokens):
    accent = tokens["color"][props.get("accent", "primary")]["value"]
    eyebrow = (
        f'<div class="eyebrow" style="color:{accent}">{html.escape(props["eyebrow"].upper())}</div>'
        if "eyebrow" in props
        else ""
    )
    return f"""
    <section class="title-block">
      {eyebrow}
      <h1>{html.escape(props["headline"])}</h1>
    </section>
    """


def render_stat_trio(props, tokens):
    cells = []
    for stat in props["stats"]:
        delta = (
            f'<div class="stat-delta" style="color:{tokens["color"]["secondary"]["value"]}">{html.escape(stat["delta"])}</div>'
            if "delta" in stat
            else ""
        )
        href = stat.get("href")
        inner = f"""
          <div class="stat-value">{html.escape(stat["value"])}</div>
          <div class="stat-label">{html.escape(stat["label"])}</div>
          {delta}
        """
        cell = f'<a class="stat" href="{html.escape(href)}">{inner}</a>' if href else f'<div class="stat">{inner}</div>'
        cells.append(cell)
    return f'<section class="stat-trio">{"".join(cells)}</section>'


RENDERERS = {"title": render_title, "stat-trio": render_stat_trio}


def main():
    comp_path = sys.argv[1] if len(sys.argv) > 1 else "composition-web.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "out-web.html"
    composition = json.loads((HERE / comp_path).read_text())
    tokens = json.loads((HERE / "tokens.json").read_text())
    assert composition["target"] == "web", "wrong target for web renderer"

    body = []
    for block in composition["blocks"]:
        renderer = RENDERERS.get(block["component"])
        if renderer is None:
            raise ValueError(f"web renderer has no component {block['component']!r}")
        body.append(renderer(block["props"], tokens))

    css = f"""
    body {{
      background: {tokens["color"]["background"]["value"]};
      color: {tokens["color"]["text"]["value"]};
      font-family: "{tokens["typography"]["family"]["value"]}", sans-serif;
      max-width: 960px;
      margin: 0 auto;
      padding: {tokens["space"]["lg"]["value"]}px;
    }}
    .title-block {{ margin-bottom: {tokens["space"]["lg"]["value"]}px; }}
    .eyebrow {{
      font-size: {tokens["typography"]["eyebrow-size"]["value"]}px;
      font-weight: bold;
      letter-spacing: 0.05em;
    }}
    h1 {{ font-size: {tokens["typography"]["headline-size"]["value"]}px; margin: {tokens["space"]["sm"]["value"]}px 0; }}
    .stat-trio {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: {tokens["space"]["md"]["value"]}px;
    }}
    .stat {{ text-decoration: none; color: inherit; display: block; }}
    .stat-value {{
      font-size: {tokens["typography"]["stat-value-size"]["value"]}px;
      font-weight: bold;
      color: {tokens["color"]["primary"]["value"]};
    }}
    .stat-label {{
      font-size: {tokens["typography"]["stat-label-size"]["value"]}px;
      color: {tokens["color"]["neutral"]["value"]};
    }}
    .stat-delta {{ font-size: {tokens["typography"]["stat-label-size"]["value"]}px; }}
    @media (max-width: 600px) {{
      .stat-trio {{ grid-template-columns: 1fr; }}
    }}
    """

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(composition["blocks"][0]["props"].get("headline", "Bindery artifact"))}</title>
<style>{css}</style>
</head>
<body>
{''.join(body)}
</body>
</html>
"""
    (HERE / out_path).write_text(html_doc)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
