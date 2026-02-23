from lxml import etree

from docxlate.handlers import latex


def test_itemize_and_enumerate_use_list_styles():
    tex = r"""
\begin{itemize}
\item Bullet one
\item Bullet two
\end{itemize}
\begin{enumerate}
\item Number one
\item Number two
\end{enumerate}
"""
    latex.run(tex)

    nonempty = [p for p in latex.doc.paragraphs if p.text.strip()]
    assert len(nonempty) >= 4
    assert nonempty[0].text.strip().startswith("Bullet one")
    assert nonempty[1].text.strip().startswith("Bullet two")
    assert nonempty[2].text.strip().startswith("Number one")
    assert nonempty[3].text.strip().startswith("Number two")
    # Ensure real Word list numbering is present, not style-only paragraphs.
    xml = [p._element.xml for p in nonempty[:4]]
    assert all("w:numPr" in pxml for pxml in xml)


def test_itemize_uses_visible_bullet_definition():
    tex = r"""
\begin{itemize}
\item Bullet one
\item Bullet two
\end{itemize}
"""
    latex.run(tex)

    paragraphs = [p for p in latex.doc.paragraphs if p.text.strip()]
    assert len(paragraphs) >= 2
    first = paragraphs[0]
    pxml = first._element.xml
    assert "w:numPr" in pxml
    num_id = pxml.split('w:numId w:val="', 1)[1].split('"', 1)[0]

    root = etree.fromstring(first.part.numbering_part.blob)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    abstract_id = root.xpath(
        f"string(.//w:num[@w:numId='{num_id}']/w:abstractNumId/@w:val)",
        namespaces=ns,
    )
    assert abstract_id
    lvl_text = root.xpath(
        f"string(.//w:abstractNum[@w:abstractNumId='{abstract_id}']/w:lvl[@w:ilvl='0']/w:lvlText/@w:val)",
        namespaces=ns,
    )
    assert lvl_text.strip()


def test_list_rendering_has_no_empty_paragraph_between_items():
    tex = r"""
\begin{itemize}
\item Alpha
\item Beta
\item Gamma
\end{itemize}
"""
    latex.run(tex)

    xml = [p._element.xml for p in latex.doc.paragraphs]
    empty_idx = [
        idx
        for idx, pxml in enumerate(xml)
        if "<w:pPr" not in pxml
        and "<w:r" not in pxml
        and "<w:hyperlink" not in pxml
        and "<w:drawing" not in pxml
        and "<m:oMath" not in pxml
    ]
    numbered_idx = [idx for idx, pxml in enumerate(xml) if "<w:numPr" in pxml]

    for idx in empty_idx:
        if idx == 0 or idx + 1 >= len(xml):
            continue
        assert not (
            idx - 1 in numbered_idx and idx + 1 in numbered_idx
        ), "unexpected empty paragraph between list items"
