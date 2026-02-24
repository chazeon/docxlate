import pytest
from pydantic import ValidationError

from docxlate.config import validate_runtime_config


def test_validate_runtime_config_accepts_known_fields():
    data = {
        "bibliography_template": "<< fields.title >>",
        "figure_caption_template": r"\textbf{Figure. << x >>} << caption >>",
        "bibliography_numbering": "none",
        "bibliography_indent_in": 0.4,
        "bibliography_et_al_limit": 2,
        "citation_compress_ranges": True,
        "citation_range_min_run": 3,
        "title_render_policy": "auto",
        "parse_skip_packages": ["fontspec"],
        "parse_skip_usepackage_paths": ["styles/proposal-compact"],
        "mathml2omml_xsl_path": "/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL",
        "wrapfigure_dist_left_in": 0.2,
        "wrapfigure_dist_right_in": 0.3,
        "wrapfigure_dist_top_in": 0.05,
        "wrapfigure_dist_bottom_in": 0.06,
        "wrapfigure_textbox_inset_left_in": 0.01,
        "wrapfigure_textbox_inset_right_in": 0.02,
        "wrapfigure_textbox_inset_top_in": 0.03,
        "wrapfigure_textbox_inset_bottom_in": 0.04,
        "wrapfigure_caption_gap_in": 0.2,
    }
    validated = validate_runtime_config(data)
    assert validated["bibliography_template"] == "<< fields.title >>"
    assert validated["figure_caption_template"] == r"\textbf{Figure. << x >>} << caption >>"
    assert validated["bibliography_numbering"] == "none"
    assert validated["bibliography_indent_in"] == 0.4
    assert validated["bibliography_et_al_limit"] == 2
    assert validated["citation_compress_ranges"] is True
    assert validated["citation_range_min_run"] == 3
    assert validated["title_render_policy"] == "auto"
    assert validated["parse_skip_packages"] == ["fontspec"]
    assert validated["parse_skip_usepackage_paths"] == ["styles/proposal-compact"]
    assert validated["mathml2omml_xsl_path"] == "/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL"
    assert validated["wrapfigure_dist_left_in"] == 0.2
    assert validated["wrapfigure_dist_right_in"] == 0.3
    assert validated["wrapfigure_dist_top_in"] == 0.05
    assert validated["wrapfigure_dist_bottom_in"] == 0.06
    assert validated["wrapfigure_textbox_inset_left_in"] == 0.01
    assert validated["wrapfigure_textbox_inset_right_in"] == 0.02
    assert validated["wrapfigure_textbox_inset_top_in"] == 0.03
    assert validated["wrapfigure_textbox_inset_bottom_in"] == 0.04
    assert validated["wrapfigure_caption_gap_in"] == 0.2


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


def test_validate_runtime_config_rejects_negative_wrap_distances():
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_dist_left_in": -0.1})


def test_validate_runtime_config_rejects_negative_textbox_insets():
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_textbox_inset_left_in": -0.1})


def test_validate_runtime_config_rejects_negative_caption_gap():
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_caption_gap_in": -0.1})
