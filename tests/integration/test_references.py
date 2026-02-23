from docxlate.handlers import latex


def test_label_and_ref_internal_link():
    tex = r"\section{A}\label{sec:a} See \ref{sec:a}."

    latex.run(tex)

    xml = "".join(p._element.xml for p in latex.doc.paragraphs)
    assert "w:hyperlink" in xml
    assert 'w:anchor="ref_sec_a"' in xml


def test_eqref_formats_parenthesized_reference():
    latex.context["refs"] = {"eq:x": {"ref_num": "1.1"}}
    tex = r"\begin{equation}a=b\label{eq:x}\end{equation} See \eqref{eq:x}."

    latex.run(tex)

    full_text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "(1.1)" in full_text


def test_missing_reference_emits_warning_and_placeholder():
    latex.run(r"See \ref{missing}.")

    warnings = latex.context.get("warnings", [])
    assert warnings
    assert "missing" in warnings[0]


def test_href_creates_external_link():
    latex.run(r"Open \href{https://example.com}{Example}.")

    xml = "".join(p._element.xml for p in latex.doc.paragraphs)
    assert "w:hyperlink" in xml
    rels = latex.doc.part.rels
    assert any(
        rel.reltype.endswith("/hyperlink") and rel.target_ref == "https://example.com"
        for rel in rels.values()
    )


def test_hyperref_uses_custom_link_text():
    latex.run(r"\section{A}\label{sec:a} Jump: \hyperref[sec:a]{go there}")

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "go there" in text
    xml = "".join(p._element.xml for p in latex.doc.paragraphs)
    assert 'w:anchor="ref_sec_a"' in xml


def test_href_preserves_nested_math_text():
    latex.run(r"Open \href{https://example.com}{Value $E=mc^2$}.")

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "Value" in text
    assert "E=mc^2" in text
    rels = latex.doc.part.rels
    assert any(
        rel.reltype.endswith("/hyperlink") and rel.target_ref == "https://example.com"
        for rel in rels.values()
    )


def test_href_preserves_nested_bold_style():
    latex.run(r"\href{https://example.com}{\textbf{Name Here}}")

    para = latex.doc.paragraphs[0]
    assert "Name Here" in para.text
    xml = para._element.xml
    assert "w:hyperlink" in xml
    assert "<w:b/>" in xml or "<w:b " in xml
