from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

_LEFT_IN = 1.0
_HEIGHT_IN = 1.8


def _hexcolor(tokens, name):
    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


def layout(slide, props: dict, tokens: dict, y: float = 2.6) -> float:
    stats = props["stats"]
    gap = Inches(0.5)
    col_width = (Inches(8) - gap * (len(stats) - 1)) // len(stats) if len(stats) > 1 else Inches(8)

    for i, stat in enumerate(stats):
        left = Inches(_LEFT_IN) + i * (col_width + gap)

        rule = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, left, Inches(y), col_width, Emu(12700),
        )
        for attr in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(rule.text_frame, attr, 0)
        rule.fill.solid()
        rule.fill.fore_color.rgb = _hexcolor(tokens, "neutral")
        rule.line.fill.background()

        box = slide.shapes.add_textbox(left, Inches(y) + Emu(50800), col_width, Inches(_HEIGHT_IN))
        tf = box.text_frame
        tf.word_wrap = True
        p_val = tf.paragraphs[0]
        p_val.text = stat["value"]
        p_val.font.size = Pt(int(tokens["typography"]["stat-value-size"]["value"]))
        p_val.font.bold = True
        p_val.font.name = tokens["typography"]["family"]["value"]
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

    return _HEIGHT_IN + 0.3
