from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

_LEFT_IN = 1.0
_HEIGHT_IN = 1.4


def _hexcolor(tokens, name):
    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    box = slide.shapes.add_textbox(Inches(_LEFT_IN), Inches(y), Inches(8), Inches(_HEIGHT_IN))
    tf = box.text_frame
    tf.word_wrap = True

    p_asset = tf.paragraphs[0]
    p_asset.text = props["asset"].upper()
    p_asset.font.size = Pt(int(tokens["typography"]["eyebrow-size"]["value"]))
    p_asset.font.bold = True
    p_asset.font.color.rgb = _hexcolor(tokens, props.get("accent", "secondary"))

    p_caption = tf.add_paragraph()
    p_caption.text = props["caption"]
    p_caption.font.size = Pt(int(tokens["typography"]["body-size"]["value"]))
    p_caption.font.name = tokens["typography"]["family"]["value"]
    p_caption.font.italic = True
    p_caption.font.color.rgb = _hexcolor(tokens, "text")

    return _HEIGHT_IN + 0.3
