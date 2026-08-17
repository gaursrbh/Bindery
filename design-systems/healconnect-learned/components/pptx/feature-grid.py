from pptx.util import Inches, Pt


def _hexcolor(tokens, name):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


_HEIGHT_IN = 1.8


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    features = props["features"]
    col_width = Inches(9.0 / len(features))
    for i, feature in enumerate(features):
        left = Inches(0.6) + i * col_width
        box = slide.shapes.add_textbox(left, Inches(y), col_width - Inches(0.2), Inches(_HEIGHT_IN))
        tf = box.text_frame
        tf.word_wrap = True

        p_title = tf.paragraphs[0]
        p_title.text = feature["title"]
        p_title.font.size = Pt(int(tokens["typography"]["eyebrow-size"]["value"]))
        p_title.font.bold = True
        p_title.font.color.rgb = _hexcolor(tokens, "primary")

        p_desc = tf.add_paragraph()
        p_desc.text = feature["description"]
        p_desc.font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
        p_desc.font.color.rgb = _hexcolor(tokens, "text")

    return _HEIGHT_IN + 0.2
