from docxlate.handlers import latex


def test_unknown_macro_keeps_inner_text_and_does_not_crash():
    latex.run(r"Start \\unknownmacro{inner text} End")

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "Start" in text
    assert "inner text" in text
    assert "End" in text
