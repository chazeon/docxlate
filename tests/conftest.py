import pytest
from pathlib import Path

from docxlate.handlers import latex

OFFICE_XSL_CANDIDATES = [
    Path("/Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl"),
    Path("/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL"),
]


def _resolve_xsl_path() -> Path | None:
    env_path = Path(__import__("os").environ.get("DOCXLATE_MML2OMML_XSL", "")).expanduser()
    if str(env_path) and env_path.exists():
        return env_path
    for p in OFFICE_XSL_CANDIDATES:
        if p.exists():
            return p
    return None


@pytest.fixture(autouse=True)
def reset_latex_bridge_state():
    latex.reset_document()
    latex.context.clear()
    xsl = _resolve_xsl_path()
    if xsl is not None:
        latex.context["mathml2omml_xsl_path"] = str(xsl.resolve())
    yield
    latex.reset_document()
    latex.context.clear()
