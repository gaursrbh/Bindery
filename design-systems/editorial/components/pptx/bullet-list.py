from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

_LEFT_IN = 1.0


def _hexcolor(tokens, name):
    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    n_lines = len(props["items"]) + (1 if "heading" in props else 0)
    height_in = min(3.5, 0.4 * n_lines + 0.4)
    box = slide.shapes.add_textbox(Inches(_LEFT_IN), Inches(y), Inches(8), Inches(height_in))
    tf = box.text_frame
    tf.word_wrap = True

    first = True
    if "heading" in props:
        p = tf.paragraphs[0]
        p.text = props["heading"]
        p.font.size = Pt(int(tokens["typography"]["subhead-size"]["value"]))
        p.font.bold = True
        p.font.name = tokens["typography"]["family"]["value"]
        p.font.color.rgb = _hexcolor(tokens, "primary")
        first = False

    for item in props["items"]:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        # Editorial style: an em-dash instead of a bullet dot.
        p.text = f"—  {item}"
        p.font.size = Pt(int(tokens["typography"]["body-size"]["value"]))
        p.font.color.rgb = _hexcolor(tokens, "text")
        p.space_after = Pt(6)

    return height_in + 0.3
