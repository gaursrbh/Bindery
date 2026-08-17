from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

_LEFT_IN = 1.0
_HEADING_H_IN = 0.4
_ROW_H_IN = 0.6


def _hexcolor(tokens, name):
    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    heading = props.get("heading")
    rows = props["rows"]
    cursor = y

    if heading:
        box = slide.shapes.add_textbox(Inches(_LEFT_IN), Inches(cursor), Inches(8), Inches(_HEADING_H_IN))
        p = box.text_frame.paragraphs[0]
        p.text = heading
        p.font.size = Pt(int(tokens["typography"]["eyebrow-size"]["value"]))
        p.font.bold = True
        p.font.name = tokens["typography"]["family"]["value"]
        p.font.color.rgb = _hexcolor(tokens, "secondary")
        cursor += _HEADING_H_IN + 0.1

    n_rows = len(rows)
    table_h_in = _ROW_H_IN * n_rows
    graphic_frame = slide.shapes.add_table(
        n_rows, 2, Inches(_LEFT_IN), Inches(cursor), Inches(8), Inches(table_h_in)
    )
    table = graphic_frame.table
    for i, row in enumerate(rows):
        cell_signal = table.cell(i, 0)
        cell_signal.text = row["signal"]
        p_signal = cell_signal.text_frame.paragraphs[0]
        p_signal.font.size = Pt(int(tokens["typography"]["body-size"]["value"]))
        p_signal.font.name = tokens["typography"]["family"]["value"]
        p_signal.font.color.rgb = _hexcolor(tokens, "text")

        cell_action = table.cell(i, 1)
        cell_action.text = row["action"]
        p_action = cell_action.text_frame.paragraphs[0]
        p_action.font.size = Pt(int(tokens["typography"]["body-size"]["value"]))
        p_action.font.name = tokens["typography"]["family"]["value"]
        p_action.font.bold = True
        p_action.font.color.rgb = _hexcolor(tokens, "primary")

    cursor += table_h_in + 0.3
    return cursor - y
