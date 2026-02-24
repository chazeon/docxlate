from docxlate.handlers import latex
from lxml import etree


def _nonempty_runs(paragraph):
    return [run for run in paragraph.runs if run.text and run.text.strip()]


def test_declaration_style_affects_following_text_only():
    latex.run(r"{A \bfseries B}")
    para = latex.doc.paragraphs[0]
    runs = _nonempty_runs(para)
    assert any("A" in run.text and not run.bold for run in runs)
    assert any("B" in run.text and run.bold for run in runs)


def test_group_scope_pop_restores_previous_style():
    latex.run(r"X {\itshape Y} Z")
    para = latex.doc.paragraphs[0]
    runs = _nonempty_runs(para)
    assert any("X" in run.text and not run.italic for run in runs)
    assert any("Y" in run.text and run.italic for run in runs)
    assert any("Z" in run.text and not run.italic for run in runs)


def test_nested_declaration_override_then_restore():
    latex.run(r"{\bfseries A {\mdseries B} C}")
    para = latex.doc.paragraphs[0]
    runs = _nonempty_runs(para)
    assert any("A" in run.text and run.bold for run in runs)
    assert any("B" in run.text and not run.bold for run in runs)
    assert any("C" in run.text and run.bold for run in runs)


def test_inline_style_composes_with_declaration_scope():
    latex.run(r"{\bfseries A \textit{B} C}")
    para = latex.doc.paragraphs[0]
    runs = _nonempty_runs(para)
    assert any("A" in run.text and run.bold and not run.italic for run in runs)
    assert any("B" in run.text and run.bold and run.italic for run in runs)
    assert any("C" in run.text and run.bold and not run.italic for run in runs)


def test_color_declaration_affects_following_text_only():
    latex.run(r"{A \color{red} B} C")
    para = latex.doc.paragraphs[0]
    runs = _nonempty_runs(para)
    assert "A" in para.text and "B" in para.text and "C" in para.text
    assert any("A" in run.text and run.font.color.rgb is None for run in runs)
    assert any("B" in run.text and run.font.color.rgb is not None for run in runs)
    assert any("C" in run.text and run.font.color.rgb is None for run in runs)


def test_color_declaration_applies_to_inline_math_and_not_following_text():
    latex.run(r"{\color{red} $x$} Y")
    para = latex.doc.paragraphs[0]
    runs = _nonempty_runs(para)
    assert "Y" in para.text
    assert "FF0000" in para._element.xml
    assert any("Y" in run.text and run.font.color.rgb is None for run in runs)


def test_paragraph_runin_body_emits_explicit_bold_reset():
    latex.run(r"\paragraph{Title} body")
    para = latex.doc.paragraphs[0]
    xml = para._element.xml
    assert "Title body" in para.text
    assert "<w:b/>" in xml or "<w:b " in xml
    assert 'w:val="0"' in xml


def test_mdseries_emits_explicit_bold_off_in_bold_scope():
    latex.run(r"{\bfseries A {\mdseries RESETBOLD} C}")
    para = latex.doc.paragraphs[0]
    root = etree.fromstring(para._element.xml.encode("utf-8"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    assert root.xpath(".//w:rPr/w:b", namespaces=ns)
    assert root.xpath(".//w:rPr/w:b[@w:val='0']", namespaces=ns)


def test_upshape_emits_explicit_italic_off_in_italic_scope():
    latex.run(r"{\itshape A {\upshape RESETITALIC} C}")
    para = latex.doc.paragraphs[0]
    root = etree.fromstring(para._element.xml.encode("utf-8"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    assert root.xpath(".//w:rPr/w:i", namespaces=ns)
    assert root.xpath(".//w:rPr/w:i[@w:val='0']", namespaces=ns)


def test_normalfont_emits_explicit_off_toggles_in_styled_scope():
    latex.run(r"{\bfseries\itshape A {\normalfont RESETALL} C}")
    para = latex.doc.paragraphs[0]
    root = etree.fromstring(para._element.xml.encode("utf-8"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    assert root.xpath(".//w:rPr/w:b[@w:val='0']", namespaces=ns)
    assert root.xpath(".//w:rPr/w:i[@w:val='0']", namespaces=ns)


def test_math_fallback_text_emits_explicit_bold_reset():
    latex.context["mathml2omml_xsl_path"] = "/tmp/does-not-exist-mathml2omml.xsl"
    latex.run(r"{\bfseries {\mdseries $x$}}")
    para = latex.doc.paragraphs[0]
    root = etree.fromstring(para._element.xml.encode("utf-8"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    assert root.xpath(".//w:rPr/w:b[@w:val='0']", namespaces=ns)
