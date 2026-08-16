"""Text-frame overflow measurement — mainPRD R4, M0-spec.md §4.1 step 4.

python-pptx does not detect overflow itself; this computes whether a
shape's paragraphs need more vertical space than the frame provides,
using font metrics directly (no rendering round-trip).
"""

from __future__ import annotations

from PIL import ImageFont

from bindery.render.errors import RenderError

_EMU_PER_PT = 12700
_DEFAULT_MARGIN_LR_EMU = 91440  # python-pptx default 0.1in
_DEFAULT_MARGIN_TB_EMU = 45720  # python-pptx default 0.05in
_LINE_SPACING = 1.2
_DEFAULT_FONT_SIZE_PT = 12


def _load_font(family: str, size_pt: int) -> ImageFont.FreeTypeFont:
    for candidate in (family, family.replace(" ", "")):
        try:
            return ImageFont.truetype(candidate, size_pt)
        except OSError:
            continue
    return ImageFont.load_default(size=size_pt)


def _wrapped_line_count(text: str, font: ImageFont.FreeTypeFont, max_width_pt: float) -> int:
    words = text.split()
    if not words:
        return 1
    lines = 1
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.getlength(candidate) <= max_width_pt:
            current = candidate
        else:
            lines += 1
            current = word
    return lines


def check_overflow(shape, font_family: str, block_index: int, prop: str) -> None:
    """Raise RenderError if `shape`'s text frame needs more vertical space
    than its geometry provides, for the text/font sizes actually placed."""
    tf = shape.text_frame
    margin_l = tf.margin_left if tf.margin_left is not None else _DEFAULT_MARGIN_LR_EMU
    margin_r = tf.margin_right if tf.margin_right is not None else _DEFAULT_MARGIN_LR_EMU
    margin_t = tf.margin_top if tf.margin_top is not None else _DEFAULT_MARGIN_TB_EMU
    margin_b = tf.margin_bottom if tf.margin_bottom is not None else _DEFAULT_MARGIN_TB_EMU

    usable_width_pt = (shape.width - margin_l - margin_r) / _EMU_PER_PT
    usable_height_pt = (shape.height - margin_t - margin_b) / _EMU_PER_PT

    total_height_pt = 0.0
    for paragraph in tf.paragraphs:
        size_pt = paragraph.font.size.pt if paragraph.font.size else _DEFAULT_FONT_SIZE_PT
        font = _load_font(font_family, int(round(size_pt)))
        lines = _wrapped_line_count(paragraph.text, font, usable_width_pt)
        total_height_pt += lines * size_pt * _LINE_SPACING

    if total_height_pt > usable_height_pt:
        raise RenderError(
            block_index,
            prop,
            f"text overflows frame: needs {total_height_pt:.1f}pt of height, "
            f"frame provides {usable_height_pt:.1f}pt",
        )
