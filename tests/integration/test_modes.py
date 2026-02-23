import pytest

from docxlate.handlers import latex


@pytest.mark.xfail(reason="Strict/permissive mode controls are not implemented yet")
def test_unknown_macro_permissive_vs_strict_modes():
    tex = r"Before \\unknownmacro{value} after"

    latex.context["mode"] = "permissive"
    latex.run(tex)
    permissive_text = "\n".join(p.text for p in latex.doc.paragraphs)

    latex.reset_document()
    latex.context.clear()
    latex.context["mode"] = "strict"

    with pytest.raises(Exception):
        latex.run(tex)

    assert "Before" in permissive_text
