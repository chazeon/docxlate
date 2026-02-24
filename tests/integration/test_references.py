import pytest
from pathlib import Path

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


def test_href_preserves_outer_bold_style():
    latex.run(r"\textbf{\href{https://example.com}{Name Here}}")

    para = latex.doc.paragraphs[0]
    assert "Name Here" in para.text
    xml = para._element.xml
    assert "w:hyperlink" in xml
    assert "<w:b/>" in xml or "<w:b " in xml


def test_href_bold_equivalent_for_both_nesting_orders():
    latex.run(
        r"\href{https://example.com}{\textbf{Inner Bold}} "
        r"\textbf{\href{https://example.com}{Outer Bold}}"
    )
    para = latex.doc.paragraphs[0]
    assert "Inner Bold" in para.text
    assert "Outer Bold" in para.text
    xml = para._element.xml
    # Both links should keep bold formatting regardless of nesting order.
    assert xml.count("<w:hyperlink") >= 2
    assert xml.count("<w:b/>") + xml.count("<w:b ") >= 2


def test_href_mdseries_emits_explicit_bold_reset_in_bold_scope():
    latex.run(r"{\bfseries \href{https://example.com}{{\mdseries Link}}}")

    para = latex.doc.paragraphs[0]
    assert "Link" in para.text
    xml = para._element.xml
    assert "w:hyperlink" in xml
    assert '<w:b w:val="0"' in xml


def test_nested_hyperlinks_raise_error():
    with pytest.raises(RuntimeError, match="Nested hyperlinks are not supported"):
        latex.run(r"\href{https://a.example}{Outer \href{https://b.example}{Inner}}")


def test_invalid_href_target_is_rendered_as_plain_text_without_relationship():
    latex.run(r"\href{<plasTeX.TeXFragment object at 0x1>}{Bad Link}")

    para = latex.doc.paragraphs[0]
    assert "Bad Link" in para.text
    xml = para._element.xml
    assert "w:hyperlink" not in xml
    rels = latex.doc.part.rels
    assert not any("plasTeX.TeXFragment" in getattr(rel, "target_ref", "") for rel in rels.values())
    warnings = latex.context.get("warnings", [])
    assert any("Skipped invalid hyperlink target" in w for w in warnings)


def test_bibliography_e2e_from_bbl_file_handles_tokens(tmp_path):
    tex_path = tmp_path / "doc.tex"
    tex_path.write_text(r"\cite{KeyA}.", encoding="utf-8")
    (tmp_path / "doc.aux").write_text(r"\abx@aux@cite{0}{KeyA}", encoding="utf-8")
    (tmp_path / "doc.bbl").write_text(
        Path("tests/fixtures/bbl/sample.bbl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    latex.context["tex_path"] = str(tex_path)
    latex.context.setdefault("plugins", {}).setdefault("bibliography", {})[
        "template"
    ] = r"\textquotedblleft{}<< fields.title >>\textquotedblright{} << fields.pages >>."
    latex.run(tex_path.read_text(encoding="utf-8"))

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "“A sample article”" in text
    assert "10–20" in text
    bib_para = next(p for p in latex.doc.paragraphs if "A sample article" in p.text)
    bib_xml = bib_para._element.xml
    assert "“" in bib_xml
    assert "”" in bib_xml


def test_bibliography_template_raw_tex_quotes_e2e(tmp_path):
    tex_path = tmp_path / "doc.tex"
    tex_path.write_text(r"\cite{KeyA}.", encoding="utf-8")
    (tmp_path / "doc.aux").write_text(r"\abx@aux@cite{0}{KeyA}", encoding="utf-8")
    (tmp_path / "doc.bbl").write_text(
        Path("tests/fixtures/bbl/sample.bbl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    latex.context["tex_path"] = str(tex_path)
    latex.context.setdefault("plugins", {}).setdefault("bibliography", {})[
        "template"
    ] = r"``<< fields.title >>''."
    latex.run(tex_path.read_text(encoding="utf-8"))

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "“A sample article”." in text


def test_bibliography_name_macro_default_renders_bibinitperiod(tmp_path):
    tex_path = tmp_path / "doc.tex"
    tex_path.write_text(r"\cite{KeyN}.", encoding="utf-8")
    (tmp_path / "doc.aux").write_text(r"\abx@aux@cite{0}{KeyN}", encoding="utf-8")
    (tmp_path / "doc.bbl").write_text(
        r"""
\refsection{0}
\entry{KeyN}{article}{}
\name{author}{1}{}{%
  {{hash=a}{family={Zhang},given={Zhen},giveni={Z\bibinitperiod}}}%
}
\field{title}{Name Test}
\endentry
\endrefsection
""".strip(),
        encoding="utf-8",
    )

    latex.context["tex_path"] = str(tex_path)
    latex.context.setdefault("plugins", {}).setdefault("bibliography", {})[
        "template"
    ] = r"<< author_names[0].family >>, << author_names[0].giveni >>."
    latex.run(tex_path.read_text(encoding="utf-8"))

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "Zhang, Z." in text


def test_bibliography_name_macro_replacement_is_configurable(tmp_path):
    tex_path = tmp_path / "doc.tex"
    tex_path.write_text(r"\cite{KeyN}.", encoding="utf-8")
    (tmp_path / "doc.aux").write_text(r"\abx@aux@cite{0}{KeyN}", encoding="utf-8")
    (tmp_path / "doc.bbl").write_text(
        r"""
\refsection{0}
\entry{KeyN}{article}{}
\name{author}{1}{}{%
  {{hash=a}{family={Zhang},given={Zhen},giveni={Z\bibinitperiod}}}%
}
\field{title}{Name Test}
\endentry
\endrefsection
""".strip(),
        encoding="utf-8",
    )

    latex.context["tex_path"] = str(tex_path)
    latex.context.setdefault("plugins", {}).setdefault("bibliography", {})[
        "macro_replacements"
    ] = {"bibinitperiod": "·"}
    latex.context.setdefault("plugins", {}).setdefault("bibliography", {})[
        "template"
    ] = r"<< author_names[0].family >>, << author_names[0].giveni >>."
    latex.run(tex_path.read_text(encoding="utf-8"))

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    assert "Zhang, Z·" in text
