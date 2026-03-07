from __future__ import annotations

import base64
from pathlib import Path

from docxlate.handlers import latex


def _write_png(path: Path):
    data = (
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+X2w0AAAAASUVORK5CYII="
    )
    path.write_bytes(base64.b64decode(data))


def test_table_specs_use_render_policy_for_table_and_tabular():
    specs = latex.macro_specs
    assert specs["table"].policy == "render"
    assert specs["tabular"].policy == "render"
    assert specs["multicolumn"].policy == "stub"


def test_tabular_renders_native_word_table_with_cell_content():
    latex.run(r"\begin{tabular}{c l}Alpha & \textbf{Beta}\\Gamma & Delta\end{tabular}")

    assert len(latex.doc.tables) == 1
    table = latex.doc.tables[0]
    assert len(table.rows) == 2
    assert len(table.columns) == 2
    text = "\n".join(cell.text for row in table.rows for cell in row.cells)
    assert "Alpha" in text
    assert "Beta" in text
    assert "Gamma" in text
    assert "Delta" in text

    tbl_xml = table._tbl.xml
    assert "<w:tblStyle" in tbl_xml


def test_tabular_uses_plugin_style_candidates_and_autofit_override():
    latex.context["plugins"] = {
        "table": {
            "style_candidates": ["MissingStyleName", "Table Grid"],
            "fallback_style": "Table Grid",
            "autofit": False,
        }
    }
    latex.run(r"\begin{tabular}{c}A\end{tabular}")

    table = latex.doc.tables[0]
    assert table.style is not None
    assert table.style.name == "Table Grid"
    assert table.autofit is False


def test_table_caption_and_label_register_reference_with_aux_number():
    latex.context["refs"] = {"tab:demo": {"ref_num": "4.2"}}
    tex = (
        r"\begin{table}"
        r"\begin{tabular}{c}A\end{tabular}"
        r"\caption{My Caption}\label{tab:demo}"
        r"\end{table} See \ref{tab:demo}."
    )
    latex.run(tex)

    # caption paragraph contains table number from refs
    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "Table 4.2." in text
    assert "My Caption" in text
    assert "4.2" in text

    xml = "".join(p._element.xml for p in latex.doc.paragraphs)
    assert 'w:anchor="ref_tab_demo"' in xml


def test_tabular_keeps_math_and_image_inside_cells(tmp_path):
    image_path = tmp_path / "sample.png"
    _write_png(image_path)
    tex_path = tmp_path / "doc.tex"
    tex_path.write_text("dummy")
    latex.context["tex_path"] = str(tex_path)

    tex = rf"\begin{{tabular}}{{c c}}$E=mc^2$ & \includegraphics{{{image_path.name}}}\end{{tabular}}"
    latex.run(tex)

    table = latex.doc.tables[0]
    left_xml = table.cell(0, 0)._tc.xml
    right_xml = table.cell(0, 1)._tc.xml
    assert "<m:oMath" in left_xml or "<math" in table.cell(0, 0).text
    assert "<a:blip" in right_xml


def test_tabular_multicolumn_merges_cells_horizontally():
    tex = r"\begin{tabular}{c c c}A & \multicolumn{2}{c}{BC}\\D & E & F\end{tabular}"
    latex.run(tex)

    table = latex.doc.tables[0]
    xml = table._tbl.xml
    assert 'w:gridSpan w:val="2"' in xml
    assert "BC" in "\n".join(cell.text for row in table.rows for cell in row.cells)
