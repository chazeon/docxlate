import base64
from pathlib import Path

from lxml import etree

from docxlate.handlers import latex


def _write_png(path: Path):
    # 1x1 transparent PNG
    data = (
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+X2w0AAAAASUVORK5CYII="
    )
    path.write_bytes(base64.b64decode(data))


def test_figure_renders_image_and_caption(tmp_path):
    image_path = tmp_path / "sample.png"
    _write_png(image_path)

    tex_path = tmp_path / "doc.tex"
    tex_path.write_text("dummy")
    latex.context["tex_path"] = str(tex_path)

    tex = rf"""
\begin{{figure}}
\includegraphics{{{image_path.name}}}
\caption{{Figure Caption Text}}
\end{{figure}}
"""
    latex.run(tex)

    xml = "\n".join(p._element.xml for p in latex.doc.paragraphs)
    assert "<pic:pic" in xml or "<a:blip" in xml
    assert "Figure Caption Text" in "\n".join(p.text for p in latex.doc.paragraphs)


def test_caption_para_role_uses_style_table(tmp_path):
    image_path = tmp_path / "sample.png"
    _write_png(image_path)

    tex_path = tmp_path / "doc.tex"
    tex_path.write_text("dummy")
    latex.context["tex_path"] = str(tex_path)

    original = dict(latex.style_table)
    latex.style_table.update({"caption": ["Heading 2"]})
    try:
        tex = rf"""
\begin{{figure}}
\includegraphics{{{image_path.name}}}
\caption{{Figure Caption Text}}
\end{{figure}}
"""
        latex.run(tex)
    finally:
        latex.style_table = original

    caption_para = next((p for p in latex.doc.paragraphs if "Figure Caption Text" in p.text), None)
    assert caption_para is not None
    assert caption_para.style.name == "Heading 2"


def test_wrapfigure_renders_with_alignment_and_caption(tmp_path):
    image_path = tmp_path / "sample.png"
    _write_png(image_path)

    tex_path = tmp_path / "doc.tex"
    tex_path.write_text("dummy")
    latex.context["tex_path"] = str(tex_path)

    tex = rf"""
\begin{{wrapfigure}}{{r}}{{0.4\textwidth}}
\includegraphics{{{image_path.name}}}
\caption{{Wrapped Figure Caption}}
\end{{wrapfigure}}
"""
    latex.run(tex)

    xml_paragraphs = [p._element.xml for p in latex.doc.paragraphs]
    image_para_xml = next(x for x in xml_paragraphs if "<pic:pic" in x or "<a:blip" in x)
    assert image_para_xml
    image_para = next(p for p in latex.doc.paragraphs if p._element.xml == image_para_xml)
    assert "<wp:anchor" in image_para._element.xml
    assert "<wp:wrapSquare" in image_para._element.xml
    assert "<wp:align>right</wp:align>" in image_para._element.xml
    assert "<wp:inline" not in image_para._element.xml
    assert "wp:distT=" not in image_para._element.xml
    assert "wp:relativeFrom=" not in image_para._element.xml
    assert 'distT="0"' in image_para._element.xml
    assert 'relativeFrom="margin"' in image_para._element.xml
    assert "<pic:pic" in image_para._element.xml or "<a:blip" in image_para._element.xml
    # Caption should be floating too (textbox anchor), not plain body paragraph text.
    assert any(
        "http://schemas.microsoft.com/office/word/2010/wordprocessingShape" in pxml
        and "Wrapped Figure Caption" in pxml
        and "<wp:anchor" in pxml
        for pxml in xml_paragraphs
    )
    # Caption textbox can share the same anchor paragraph as the wrapped image.
    assert any(
        ("http://schemas.microsoft.com/office/word/2010/wordprocessingShape" in pxml)
        and ("Wrapped Figure Caption" in pxml)
        and ("<pic:pic" in pxml or "<a:blip" in pxml)
        for pxml in xml_paragraphs
    )


def test_wrapfigure_width_tracks_textwidth_fraction(tmp_path):
    image_path = tmp_path / "sample.png"
    _write_png(image_path)

    tex_path = tmp_path / "doc.tex"
    tex_path.write_text("dummy")
    latex.context["tex_path"] = str(tex_path)

    tex = rf"""
\begin{{wrapfigure}}{{r}}{{0.4\textwidth}}
\includegraphics{{{image_path.name}}}
\caption{{Caption}}
\end{{wrapfigure}}
"""
    latex.run(tex)

    image_para = next(
        p
        for p in latex.doc.paragraphs
        if "<wp:anchor" in p._element.xml and ("<pic:pic" in p._element.xml or "<a:blip" in p._element.xml)
    )
    root = etree.fromstring(image_para._element.xml.encode("utf-8"))
    ns = {
        "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    }
    cx = int(root.xpath("string(.//wp:extent/@cx)", namespaces=ns))

    section = latex.doc.sections[-1]
    textwidth = int(section.page_width) - int(section.left_margin) - int(section.right_margin)
    expected = int(0.4 * textwidth)
    # Allow ~5% tolerance for rounding/dpi interactions.
    assert abs(cx - expected) <= int(0.05 * textwidth)


def test_wrapfigure_does_not_insert_empty_line_before_following_text(tmp_path):
    image_path = tmp_path / "sample.png"
    _write_png(image_path)

    tex_path = tmp_path / "doc.tex"
    tex_path.write_text("dummy")
    latex.context["tex_path"] = str(tex_path)

    tex = rf"""
\begin{{wrapfigure}}{{r}}{{0.4\textwidth}}
\includegraphics{{{image_path.name}}}
\caption{{Wrapped Figure Caption}}
\end{{wrapfigure}}
Body after.
"""
    latex.run(tex)

    body_idx = next(
        (idx for idx, p in enumerate(latex.doc.paragraphs) if "Body after." in p.text),
        None,
    )
    assert body_idx is not None
    assert body_idx >= 1
    anchor_para = latex.doc.paragraphs[body_idx - 1]
    assert "<wp:anchor" in anchor_para._element.xml
    assert anchor_para.text.strip() == ""
    # No additional plain empty paragraph should be inserted between wrap anchor and body.
    if body_idx >= 2:
        between = latex.doc.paragraphs[body_idx - 2 : body_idx]
        assert not any((not p.text.strip()) and "<wp:anchor" not in p._element.xml for p in between)
