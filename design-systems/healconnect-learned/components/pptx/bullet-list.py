from pptx.util import Inches, Pt


def _hexcolor(tokens, name):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    n_lines = len(props["items"]) + (1 if "heading" in props else 0)
    height_in = min(3.5, 0.3 * n_lines + 0.3)
    box = slide.shapes.add_textbox(Inches(0.6), Inches(y), Inches(9), Inches(height_in))
    tf = box.text_frame
    tf.word_wrap = True

    first = True
    if "heading" in props:
        p = tf.paragraphs[0]
        p.text = props["heading"]
        p.font.size = Pt(int(tokens["typography"]["stat-value-size"]["value"]))
        p.font.bold = True
        p.font.color.rgb = _hexcolor(tokens, "primary")
        first = False

    for item in props["items"]:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = f"• {item}"
        p.font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
        p.font.color.rgb = _hexcolor(tokens, "text")

    return height_in + 0.2
