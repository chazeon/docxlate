from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

from docxlate.model import LinkTarget, TextSpan


def _emit_linked_span(paragraph, span: TextSpan, link: LinkTarget):
    hyperlink = _new_hyperlink_element(paragraph, link)
    if hyperlink is None:
        return False
    hyperlink.append(_new_hyperlink_run_element(span))
    paragraph._p.append(hyperlink)
    return True


def _new_hyperlink_element(paragraph, link: LinkTarget):
    hyperlink = OxmlElement("w:hyperlink")
    if link.anchor:
        hyperlink.set(qn("w:anchor"), link.anchor)
        return hyperlink
    if link.url:
        rel_id = link.rel_id
        if rel_id is None:
            rel_id = paragraph.part.relate_to(link.url, RT.HYPERLINK, is_external=True)
            link.rel_id = rel_id
        hyperlink.set(qn("r:id"), rel_id)
        return hyperlink
    return None


def _new_hyperlink_run_element(span: TextSpan):
    run = OxmlElement("w:r")
    run.append(_new_run_properties_element(span))
    text_node = OxmlElement("w:t")
    text_node.text = span.text
    run.append(text_node)
    return run


def _new_run_properties_element(span: TextSpan):
    r_pr = OxmlElement("w:rPr")
    r_style = OxmlElement("w:rStyle")
    r_style.set(qn("w:val"), span.char_role or "Hyperlink")
    r_pr.append(r_style)
    if span.style.bold:
        r_pr.append(OxmlElement("w:b"))
    if span.style.italic:
        r_pr.append(OxmlElement("w:i"))
    if span.style.small_caps:
        r_pr.append(OxmlElement("w:smallCaps"))
    r_pr.append(_new_fonts_element(span))
    return r_pr


def _new_fonts_element(span: TextSpan):
    r_fonts = OxmlElement("w:rFonts")
    if span.style.monospace:
        r_fonts.set(qn("w:ascii"), "Courier New")
        r_fonts.set(qn("w:hAnsi"), "Courier New")
        r_fonts.set(qn("w:cs"), "Courier New")
        return r_fonts
    val = "major" if span.style.theme == "major" else "minor"
    r_fonts.set(qn("w:asciiTheme"), f"{val}Ascii")
    r_fonts.set(qn("w:hAnsiTheme"), f"{val}HAnsi")
    return r_fonts
