from docx.oxml import parse_xml
from docx.oxml.ns import qn
from lxml import etree
import latex2mathml.converter
from pathlib import Path

MATHML_NAMESPACE = "http://www.w3.org/1998/Math/MathML"
OMML_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/math"

_XSLT_CACHE: dict[str, etree.XSLT] = {}
_OMML_NS = {"m": OMML_NAMESPACE}


def _get_mathml_to_omml_transform(xsl_path: str | Path):
    resolved = str(Path(xsl_path).expanduser().resolve())
    cached = _XSLT_CACHE.get(resolved)
    if cached is not None:
        return cached
    transform = etree.XSLT(etree.parse(resolved))
    _XSLT_CACHE[resolved] = transform
    return transform


def apply_theme_font(run, theme='minor'):
    """Applies Major/Minor OpenType theme attributes."""
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    val = 'major' if theme == 'major' else 'minor'
    rFonts.set(qn('w:asciiTheme'), f'{val}Ascii')
    rFonts.set(qn('w:hAnsiTheme'), f'{val}HAnsi')


def inject_omml(paragraph, latex_str, *, xsl_path: str | Path | None = None):
    """Bridge LaTeX math to Word Math (OMML) via the provided stylesheet."""
    try:
        mathml = latex2mathml.converter.convert(latex_str)
        mathml_element = etree.fromstring(mathml.encode("utf-8"))
        if not xsl_path:
            raise RuntimeError("OMML stylesheet path is not configured")
        transform = _get_mathml_to_omml_transform(xsl_path)
        omml_result = transform(mathml_element)
        _normalize_omml_script_bases(omml_result)
        omml_xml = etree.tostring(omml_result, encoding="utf-8")
        paragraph._element.append(parse_xml(omml_xml))
        return True
    except Exception:
        paragraph.add_run(f"[Math Error: {latex_str}]")
        return False


def _normalize_omml_script_bases(omml_root) -> None:
    """
    Word can render empty script bases (<m:t/>) with visible spacing holes.
    Normalize them to a zero-width placeholder to match stable producer output.
    """
    for text_node in omml_root.xpath(
        ".//m:sSub/m:e//m:t | .//m:sSup/m:e//m:t | .//m:sSubSup/m:e//m:t",
        namespaces=_OMML_NS,
    ):
        if text_node.text in (None, ""):
            text_node.text = "\u200b"
