from docx import Document
from docxlate.utils import inject_omml
from pathlib import Path
import os
import pytest


def test_inject_omml_generates_omml_element():
    xsl = os.environ.get("DOCXLATE_MML2OMML_XSL")
    if xsl:
        xsl_path = Path(xsl).expanduser()
    else:
        xsl_path = Path("/Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl")
    if not xsl_path.exists():
        pytest.skip("No OMML XSL configured; set DOCXLATE_MML2OMML_XSL to run this test")

    doc = Document()
    paragraph = doc.add_paragraph()
    inject_omml(paragraph, r"E=mc^2", xsl_path=xsl_path)
    xml = paragraph._element.xml
    assert "<m:oMath" in xml
