from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

_LEFT_IN = 1.0
_HEIGHT_IN = 2.0


def _hexcolor(tokens, name):
    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    features = props["features"]
    gap = Inches(0.4)
    col_width = (Inches(8) - gap * (len(features) - 1)) // len(features) if len(features) > 1 else Inches(8)

    for i, feature in enumerate(features):
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
        p_title = tf.paragraphs[0]
        p_title.text = feature["title"]
        p_title.font.size = Pt(int(tokens["typography"]["subhead-size"]["value"]))
        p_title.font.bold = True
        p_title.font.name = tokens["typography"]["family"]["value"]
        p_title.font.color.rgb = _hexcolor(tokens, "primary")

        p_desc = tf.add_paragraph()
        p_desc.text = feature["description"]
        p_desc.font.size = Pt(int(tokens["typography"]["body-size"]["value"]))
        p_desc.font.color.rgb = _hexcolor(tokens, "text")

    return _HEIGHT_IN + 0.3
