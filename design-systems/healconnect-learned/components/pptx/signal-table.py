from pptx.util import Inches, Pt


def _hexcolor(tokens, name):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(tokens["color"][name]["value"].lstrip("#"))


_ROW_H_IN = 0.55
_HEADING_H_IN = 0.4


def layout(slide, props: dict, tokens: dict, y: float = 2.4) -> float:
    heading = props.get("heading")
    rows = props["rows"]
    cursor = y

    if heading:
        box = slide.shapes.add_textbox(Inches(0.6), Inches(cursor), Inches(9), Inches(_HEADING_H_IN))
        p = box.text_frame.paragraphs[0]
        p.text = heading
        p.font.size = Pt(int(tokens["typography"]["eyebrow-size"]["value"]))
        p.font.bold = True
        p.font.color.rgb = _hexcolor(tokens, "secondary")
        cursor += _HEADING_H_IN + 0.1

    n_rows = len(rows)
    table_h_in = _ROW_H_IN * n_rows
    graphic_frame = slide.shapes.add_table(
        n_rows, 2, Inches(0.6), Inches(cursor), Inches(9), Inches(table_h_in)
    )
    table = graphic_frame.table
    for i, row in enumerate(rows):
        cell_signal = table.cell(i, 0)
        cell_signal.text = row["signal"]
        cell_signal.text_frame.paragraphs[0].font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
        cell_signal.text_frame.paragraphs[0].font.color.rgb = _hexcolor(tokens, "text")

        cell_action = table.cell(i, 1)
        cell_action.text = row["action"]
        cell_action.text_frame.paragraphs[0].font.size = Pt(int(tokens["typography"]["stat-label-size"]["value"]))
        cell_action.text_frame.paragraphs[0].font.bold = True
        cell_action.text_frame.paragraphs[0].font.color.rgb = _hexcolor(tokens, "primary")

    cursor += table_h_in + 0.2
    return cursor - y
