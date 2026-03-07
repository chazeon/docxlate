from __future__ import annotations

from docxlate.handlers import latex


def test_table_specs_are_registered_as_stub_policies():
    specs = latex.macro_specs

    assert "table" in specs
    assert "tabular" in specs
    assert "multicolumn" in specs
    assert specs["table"].policy == "stub"
    assert specs["tabular"].policy == "stub"
    assert specs["multicolumn"].policy == "stub"


def test_tabular_stub_keeps_cell_text_visible():
    latex.run(r"\begin{table}\begin{tabular}{c}Alpha\\Beta\end{tabular}\end{table}")

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "Alpha" in text
    assert "Beta" in text
