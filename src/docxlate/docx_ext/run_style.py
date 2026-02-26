from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

from docxlate.model import TextSpan
from docxlate.utils import apply_theme_font


def apply_text_span_style(run, span: TextSpan):
    apply_theme_font(run, span.style.theme or "minor")
    if span.style.monospace:
        run.font.name = "Courier New"
    if span.style.bold is not None:
        run.bold = span.style.bold
    if span.style.italic is not None:
        run.italic = span.style.italic
    if span.style.small_caps is not None:
        run.font.small_caps = span.style.small_caps
    if span.style.color:
        try:
            run.font.color.rgb = RGBColor.from_string(span.style.color)
        except Exception:
            pass


def new_run_properties_for_span(span: TextSpan, *, default_char_role: str | None = None):
    r_pr = OxmlElement("w:rPr")
    char_role = span.char_role or default_char_role
    if char_role:
        r_style = OxmlElement("w:rStyle")
        r_style.set(qn("w:val"), char_role)
        r_pr.append(r_style)
    _append_on_off(r_pr, "w:b", span.style.bold)
    _append_on_off(r_pr, "w:i", span.style.italic)
    _append_on_off(r_pr, "w:smallCaps", span.style.small_caps)
    if span.style.color:
        color = OxmlElement("w:color")
        color.set(qn("w:val"), span.style.color)
        r_pr.append(color)
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


def _append_on_off(r_pr, tag: str, value: bool | None):
    if value is None:
        return
    elem = OxmlElement(tag)
    if not value:
        elem.set(qn("w:val"), "0")
    r_pr.append(elem)
