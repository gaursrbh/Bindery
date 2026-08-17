from pptx.util import Inches, Pt


def _hexcolor(tokens, name):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


_HEADING_H_IN = 0.35
_STAT_H_IN = 1.6


def layout(slide, props: dict, tokens: dict, y: float = 2.6) -> float:
    heading = props.get("heading")
    stats = props["stats"]
    cursor = y

    if heading:
        box = slide.shapes.add_textbox(Inches(0.6), Inches(cursor), Inches(9), Inches(_HEADING_H_IN))
        p = box.text_frame.paragraphs[0]
        p.text = heading
        p.font.size = Pt(int(tokens["typography"]["eyebrow-size"]["value"]))
        p.font.bold = True
        p.font.color.rgb = _hexcolor(tokens, "secondary")
        cursor += _HEADING_H_IN + 0.1

    col_width = Inches(9.0 / len(stats))
    for i, stat in enumerate(stats):
        left = Inches(0.6) + i * col_width
        box = slide.shapes.add_textbox(left, Inches(cursor), col_width - Inches(0.2), Inches(_STAT_H_IN))
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

    cursor += _STAT_H_IN + 0.2
    return cursor - y
