from pptx.util import Inches, Pt


def _hexcolor(tokens, name):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


_HEIGHT_IN = 1.6


def layout(slide, props: dict, tokens: dict, y: float = 2.6) -> float:
    stats = props["stats"]
    col_width = Inches(3.0)
    for i, stat in enumerate(stats):
        left = Inches(0.6) + i * col_width
        box = slide.shapes.add_textbox(left, Inches(y), col_width - Inches(0.2), Inches(_HEIGHT_IN))
        tf = box.text_frame
        tf.word_wrap = True
        p_val = tf.paragraphs[0]
        p_val.text = stat["value"]
        p_val.font.size = Pt(int(tokens["typography"]["stat-value-size"]["value"]))
        p_val.font.bold = True
        p_val.font.color.rgb = _hexcolor(tokens, "primary")

        p_label = tf.add_paragraph()
        p_label.text = stat["label"]
        p_label.font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
        p_label.font.color.rgb = _hexcolor(tokens, "neutral")

        if "delta" in stat:
            p_delta = tf.add_paragraph()
            p_delta.text = stat["delta"]
            p_delta.font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
            p_delta.font.color.rgb = _hexcolor(tokens, "secondary")

    return _HEIGHT_IN + 0.2
