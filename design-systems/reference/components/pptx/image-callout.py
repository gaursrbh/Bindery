from pptx.util import Inches, Pt


def _hexcolor(tokens, name):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


_HEIGHT_IN = 1.2


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    box = slide.shapes.add_textbox(Inches(0.6), Inches(y), Inches(9), Inches(_HEIGHT_IN))
    tf = box.text_frame
    tf.word_wrap = True

    p_asset = tf.paragraphs[0]
    p_asset.text = f"[{props['asset']}]"
    p_asset.font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
    p_asset.font.color.rgb = _hexcolor(tokens, props.get("accent", "neutral"))

    p_caption = tf.add_paragraph()
    p_caption.text = props["caption"]
    p_caption.font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
    p_caption.font.color.rgb = _hexcolor(tokens, "text")

    return _HEIGHT_IN + 0.2
