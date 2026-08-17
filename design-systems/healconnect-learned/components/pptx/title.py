from pptx.util import Inches, Pt


def _hexcolor(tokens, name):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


_HEIGHT_IN = 1.5


def layout(slide, props: dict, tokens: dict, y: float = 0.5) -> float:
    box = slide.shapes.add_textbox(Inches(0.6), Inches(y), Inches(9), Inches(_HEIGHT_IN))
    tf = box.text_frame
    tf.word_wrap = True
    if "eyebrow" in props:
        p = tf.paragraphs[0]
        p.text = props["eyebrow"].upper()
        p.font.size = Pt(int(tokens["typography"]["eyebrow-size"]["value"]))
        p.font.color.rgb = _hexcolor(tokens, props.get("accent", "primary"))
        p.font.bold = True
        p2 = tf.add_paragraph()
    else:
        p2 = tf.paragraphs[0]
    p2.text = props["headline"]
    p2.font.size = Pt(int(tokens["typography"]["headline-size"]["value"]))
    p2.font.color.rgb = _hexcolor(tokens, "text")
    p2.font.bold = True
    return _HEIGHT_IN + 0.2
