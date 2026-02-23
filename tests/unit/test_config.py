import pytest
from pydantic import ValidationError

from docxlate.config import validate_runtime_config


def test_validate_runtime_config_accepts_known_fields():
    data = {
        "bibliography_template": "<< fields.title >>",
        "bibliography_numbering": "none",
        "bibliography_indent_in": 0.4,
        "bibliography_et_al_limit": 2,
        "citation_compress_ranges": True,
        "citation_range_min_run": 3,
        "title_render_policy": "auto",
        "parse_skip_packages": ["fontspec"],
        "parse_skip_usepackage_paths": ["styles/proposal-compact"],
        "mathml2omml_xsl_path": "/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL",
    }
    validated = validate_runtime_config(data)
    assert validated["bibliography_template"] == "<< fields.title >>"
    assert validated["bibliography_numbering"] == "none"
    assert validated["bibliography_indent_in"] == 0.4
    assert validated["bibliography_et_al_limit"] == 2
    assert validated["citation_compress_ranges"] is True
    assert validated["citation_range_min_run"] == 3
    assert validated["title_render_policy"] == "auto"
    assert validated["parse_skip_packages"] == ["fontspec"]
    assert validated["parse_skip_usepackage_paths"] == ["styles/proposal-compact"]
    assert validated["mathml2omml_xsl_path"] == "/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL"


def test_validate_runtime_config_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        validate_runtime_config({"unknown_option": 1})


def test_validate_runtime_config_rejects_non_positive_indent():
    with pytest.raises(ValidationError):
        validate_runtime_config({"bibliography_indent_in": 0})


def test_validate_runtime_config_rejects_non_positive_et_al_limit():
    with pytest.raises(ValidationError):
        validate_runtime_config({"bibliography_et_al_limit": 0})


def test_validate_runtime_config_rejects_small_citation_min_run():
    with pytest.raises(ValidationError):
        validate_runtime_config({"citation_range_min_run": 1})


def test_validate_runtime_config_rejects_invalid_title_policy():
    with pytest.raises(ValidationError):
        validate_runtime_config({"title_render_policy": "sometimes"})
