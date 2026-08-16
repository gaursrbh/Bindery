from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

_LEFT_IN = 1.0
_HEIGHT_IN = 1.9


def _hexcolor(tokens, name):
    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


def layout(slide, props: dict, tokens: dict, y: float = 0.6) -> float:
    cursor = y
    if "eyebrow" in props:
        box = slide.shapes.add_textbox(Inches(_LEFT_IN), Inches(cursor), Inches(8), Inches(0.4))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = props["eyebrow"].upper()
        p.font.size = Pt(int(tokens["typography"]["eyebrow-size"]["value"]))
        p.font.color.rgb = _hexcolor(tokens, props.get("accent", "secondary"))
        p.font.bold = True
        p.font.name = tokens["typography"]["family"]["value"]
        cursor += 0.35

        # Thin accent rule under the eyebrow — the editorial hierarchy marker.
        rule = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(_LEFT_IN), Inches(cursor), Inches(1.4), Emu(12700)
        )
        # Autoshapes get a default text frame with nonzero margins that can
        # exceed a thin decorative shape's own height, making it always
        # "overflow" — zero the margins so there's nothing to overflow.
        for attr in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(rule.text_frame, attr, 0)
        rule.fill.solid()
        rule.fill.fore_color.rgb = _hexcolor(tokens, props.get("accent", "secondary"))
        rule.line.fill.background()
        cursor += 0.15

    box = slide.shapes.add_textbox(Inches(_LEFT_IN), Inches(cursor), Inches(8), Inches(1.6))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = props["headline"]
    p.font.size = Pt(int(tokens["typography"]["headline-size"]["value"]))
    p.font.color.rgb = _hexcolor(tokens, "text")
    p.font.name = tokens["typography"]["family"]["value"]
    p.font.bold = True

    return (cursor - y) + 1.6 + 0.2
