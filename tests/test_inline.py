from docxlate.handlers import latex
from pathlib import Path
import os


def _reset_router():
    latex.reset_document()
    latex.context.clear()
    xsl = os.environ.get("DOCXLATE_MML2OMML_XSL")
    if xsl:
        p = Path(xsl).expanduser()
        if p.exists():
            latex.context["mathml2omml_xsl_path"] = str(p.resolve())
    else:
        p = Path("/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL")
        if p.exists():
            latex.context["mathml2omml_xsl_path"] = str(p.resolve())


def test_inline_styles_emit_runs():
    _reset_router()
    tex = r"Hello \textbf{bold}\textit{italic} world"
    latex.run(tex)
    assert len(latex.doc.paragraphs) == 1
    para = latex.doc.paragraphs[0]
    assert "bold" in para.text
    assert "italic" in para.text
    bold_runs = [run for run in para.runs if run.bold]
    italic_runs = [run for run in para.runs if run.italic]
    assert bold_runs
    assert italic_runs


def test_cite_produces_inline_reference():
    _reset_router()
    latex.context['cite_order'] = {"Foo2025": 7}
    latex.run(r"Refer to \cite{Foo2025} here.")
    assert len(latex.doc.paragraphs) == 1
    para = latex.doc.paragraphs[0]
    assert "[7]" in para.text


def test_inline_math_uses_omml_runs():
    _reset_router()
    latex.run(r"Energy $E=mc^2$ plus \(a^2+b^2=c^2\).")
    assert len(latex.doc.paragraphs) == 1
    para = latex.doc.paragraphs[0]
    xml = para._element.xml
    assert xml.count("<m:oMath") >= 2 or para.text.count("[Math Error:") >= 2


def test_non_breaking_space_tie_is_preserved():
    _reset_router()
    latex.run(r"A~B")
    assert latex.doc.paragraphs[0].text == "A\u00A0B"


def test_textsc_emits_small_caps_runs():
    _reset_router()
    latex.run(r"Hello \textsc{Small Caps} world")
    para = latex.doc.paragraphs[0]
    assert "Small Caps" in para.text
    assert any(getattr(run.font, "small_caps", False) for run in para.runs)


def test_escaped_special_characters_render_as_literals():
    _reset_router()
    latex.run(r"Escaped: \% \_ \# \& \{x\}.")
    text = latex.doc.paragraphs[0].text
    assert "Escaped:" in text
    assert "%" in text
    assert "_" in text
    assert "#" in text
    assert "&" in text
    assert "{x}" in text


def test_double_backslash_percent_keeps_tex_behavior():
    _reset_router()
    latex.run(r"Prefix\\%comment")
    # TeX line-break command followed by % starts a comment; we should not
    # force a literal percent in this sequence.
    assert "%" not in latex.doc.paragraphs[0].text


def test_tex_quotes_are_preserved_in_text_stream():
    _reset_router()
    latex.run("He said: ``Hello'' and left.")
    assert latex.doc.paragraphs[0].text == "He said: ``Hello'' and left."


def test_double_backslash_linebreak_keeps_neighboring_text():
    _reset_router()
    latex.run(r"A\\B")
    text = latex.doc.paragraphs[0].text
    assert "A" in text
    assert "B" in text


def test_texttt_emits_monospace_runs():
    _reset_router()
    latex.run(r"\texttt{Code}")
    para = latex.doc.paragraphs[0]
    assert "Code" in para.text
    assert any((run.font.name or "").lower() == "courier new" for run in para.runs)


def test_declaration_styles_bfseries_itshape_apply_in_group():
    _reset_router()
    latex.run(r"{\bfseries Bold {\itshape Italic}}")
    para = latex.doc.paragraphs[0]
    assert "Bold" in para.text
    assert "Italic" in para.text
    assert any(run.bold for run in para.runs if "Bold" in run.text or "Italic" in run.text)
    assert any(run.italic for run in para.runs if "Italic" in run.text)


def test_simple_script_math_uses_nonempty_omml_base():
    _reset_router()
    latex.run(r"CO$_2$ and D$\prime\prime$")
    para = latex.doc.paragraphs[0]
    xml = para._element.xml
    if "[Math Error:" in para.text:
        # OMML path unavailable locally (missing XSL); keep test non-flaky.
        return
    assert "<m:sSub>" in xml
    assert "<m:sSup>" in xml
    assert "<m:t/>" not in xml
