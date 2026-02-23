from pathlib import Path

import pytest

from docxlate.handlers import latex


def test_section_heading_maps_to_word_heading():
    tex = Path("tests/fixtures/tex/basic_section.tex").read_text()

    latex.run(tex)

    assert latex.doc.paragraphs[0].style.name == "Heading 1"
    assert latex.doc.paragraphs[0].text == "Intro"


def test_subsection_and_subsubsection_map_to_heading_levels():
    latex.run(r"\section{Top}\subsection{Mid}\subsubsection{Low}")
    nonempty = [p for p in latex.doc.paragraphs if p.text.strip()]
    assert [p.text for p in nonempty[:3]] == ["Top", "Mid", "Low"]
    assert nonempty[0].style.name == "Heading 1"
    assert nonempty[1].style.name == "Heading 2"
    assert nonempty[2].style.name == "Heading 3"


def test_inline_formatting_bold_italic():
    latex.run(r"\textbf{B} \emph{I}")

    para = latex.doc.paragraphs[0]
    assert any(run.bold for run in para.runs)
    assert any(run.italic for run in para.runs)


@pytest.mark.xfail(reason="List environment handling is not implemented yet")
def test_itemize_nesting_depth_two():
    tex = r"""
\\begin{itemize}
  \\item Top
  \\begin{itemize}
    \\item Nested
  \\end{itemize}
\\end{itemize}
"""

    latex.run(tex)

    # Placeholder assertion for future list-level semantics.
    assert any("List" in p.style.name for p in latex.doc.paragraphs)


def test_equation_block_math_injected_or_fallback():
    latex.run(r"\begin{equation}E=mc^2\end{equation}")

    para_xml = latex.doc.paragraphs[0]._element.xml
    assert "<m:oMath" in para_xml or "<math" in latex.doc.paragraphs[0].text


def test_section_body_text_is_rendered_with_plastex():
    latex.run(r"\section{Introduction} Hello world.")

    text = "\n".join(p.text for p in latex.doc.paragraphs if p.text.strip())
    assert "Introduction" in text
    assert "Hello world." in text


def test_parse_fallback_uses_document_body_when_full_parse_fails():
    tex = r"""
\documentclass{article}
\usepackage{fontspec}
\begin{document}
Hello fallback.
\end{document}
"""
    latex.run(tex)

    text = "\n".join(p.text for p in latex.doc.paragraphs if p.text.strip())
    assert "Hello fallback." in text
    warnings = latex.context.get("warnings", [])
    assert any("body-only parse fallback" in w for w in warnings)


def test_parse_fallback_warns_when_maketitle_has_no_metadata():
    tex = r"""
\documentclass{article}
\usepackage{fontspec}
\begin{document}
\maketitle
Hello fallback.
\end{document}
"""
    latex.run(tex)

    text = "\n".join(p.text for p in latex.doc.paragraphs if p.text.strip())
    assert "Hello fallback." in text
    warnings = latex.context.get("warnings", [])
    assert any("body-only parse fallback" in w for w in warnings)
    assert any("maketitle was found" in w for w in warnings)


def test_parse_fallback_still_renders_maketitle_from_preamble_metadata():
    tex = r"""
\documentclass{article}
\usepackage{fontspec}
\title{Recovered Title}
\author{Recovered Author}
\date{2026}
\begin{document}
\maketitle
Hello fallback.
\end{document}
"""
    latex.context["title_render_policy"] = "explicit"
    latex.run(tex)

    text = "\n".join(p.text for p in latex.doc.paragraphs if p.text.strip())
    assert "Recovered Title" in text
    assert "Recovered Author" in text
    assert "2026" in text
    warnings = latex.context.get("warnings", [])
    assert any("body-only parse fallback" in w for w in warnings)
    assert not any("maketitle was found" in w for w in warnings)


def test_parse_skip_packages_avoids_known_preamble_failure():
    tex = r"""
\documentclass{article}
\usepackage{fontspec}
\begin{document}
Hello no fallback.
\end{document}
"""
    latex.context["parse_skip_packages"] = ["fontspec"]
    latex.run(tex)

    text = "\n".join(p.text for p in latex.doc.paragraphs if p.text.strip())
    assert "Hello no fallback." in text
    warnings = latex.context.get("warnings", [])
    assert any("Skipped usepackage for parser compatibility: fontspec" in w for w in warnings)
    assert not any("body-only parse fallback" in w for w in warnings)


def test_preamble_only_parse_with_text_nodes_triggers_body_fallback():
    # Combination crafted to produce noisy preamble parse while leaving body intact.
    tex = r"""
\documentclass{article}
\usepackage{styles/proposal-compact}
\usepackage{fontspec}
\begin{document}
\section{Recovered}
Body survives fallback.
\end{document}
"""
    latex.context["parse_skip_usepackage_paths"] = ["styles/proposal-compact"]
    latex.run(tex)

    text = "\n".join(p.text for p in latex.doc.paragraphs if p.text.strip())
    assert "Recovered" in text
    assert "Body survives fallback." in text
    warnings = latex.context.get("warnings", [])
    assert any("Skipped usepackage for parser compatibility: styles/proposal-compact" in w for w in warnings)
    assert any("body-only parse fallback" in w for w in warnings)


def test_section_heading_with_inline_math_renders_text_and_math():
    latex.run(r"\section{Energy $E=mc^2$}")

    nonempty = [p for p in latex.doc.paragraphs if p.text.strip()]
    assert nonempty
    heading = nonempty[0]
    assert "Energy" in heading.text
    assert "<m:oMath" in heading._element.xml or "<math" in heading.text


def test_paragraph_heading_with_inline_math_renders_math():
    latex.run(r"\paragraph{SMG: \(V_S\), \(V_P\)} Body text.")

    nonempty = [p for p in latex.doc.paragraphs if p.text.strip()]
    assert nonempty
    assert len(nonempty) == 1
    heading_para = nonempty[0]
    assert "SMG:" in heading_para.text
    assert "Body text." in heading_para.text
    assert (
        heading_para._element.xml.count("<m:oMath") >= 2
        or heading_para.text.count("<math") >= 2
    )
    assert 'w:firstLine="0"' in heading_para._element.xml
    assert 'w:left="0"' in heading_para._element.xml


def test_paragraph_heading_does_not_force_trailing_dot():
    latex.run(r"\paragraph{Overview} Body.")
    para = next((p for p in latex.doc.paragraphs if p.text.strip()), None)
    assert para is not None
    normalized = " ".join(para.text.split())
    assert "Overview Body." in normalized
    assert "Overview. Body." not in para.text


@pytest.mark.parametrize(
    "policy,metadata_in_body,has_maketitle,expect_title",
    [
        ("explicit", False, False, False),
        ("explicit", False, True, True),
        ("explicit", True, False, False),
        ("explicit", True, True, True),
        ("auto", False, False, True),
        ("auto", False, True, True),
        ("auto", True, False, True),
        ("auto", True, True, True),
        ("always", False, False, True),
        ("always", False, True, True),
        ("always", True, False, True),
        ("always", True, True, True),
    ],
)
def test_front_matter_render_policy_combinations(
    policy, metadata_in_body, has_maketitle, expect_title
):
    latex.context["title_render_policy"] = policy
    preamble = r"\title{My \textbf{Paper}}\author{Alice \and Bob}\date{2026}"
    body_meta = r"\title{My \textbf{Paper}}\author{Alice \and Bob}\date{2026} "
    body = "Body."
    if has_maketitle:
        body = r"\maketitle " + body
    tex = (body_meta if metadata_in_body else preamble) + body

    latex.run(tex)

    nonempty = [p for p in latex.doc.paragraphs if p.text.strip()]
    text = "\n".join(p.text for p in nonempty)
    if expect_title:
        assert "My Paper" in text
        assert "Alice, Bob" in text
        assert "2026" in text
    else:
        assert "My Paper" not in text
        assert "Alice, Bob" not in text
        assert "2026" not in text
    assert "Body." in text
