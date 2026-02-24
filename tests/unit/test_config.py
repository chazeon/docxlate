import pytest
from pydantic import ValidationError

from docxlate.config import SideBox, validate_runtime_config


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
        "wrap": [0.05, 0.3, 0.06, 0.2],
        "inset": {"left": 0.01, "right": 0.02, "top": 0.03, "bottom": 0.04},
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
    assert validated["wrap"]["left"] == 0.2
    assert validated["wrap"]["right"] == 0.3
    assert validated["wrap"]["top"] == 0.05
    assert validated["wrap"]["bottom"] == 0.06
    assert validated["inset"]["left"] == 0.01
    assert validated["inset"]["right"] == 0.02
    assert validated["inset"]["top"] == 0.03
    assert validated["inset"]["bottom"] == 0.04
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
        validate_runtime_config({"wrap": -0.1})


def test_validate_runtime_config_rejects_negative_textbox_insets():
    with pytest.raises(ValidationError):
        validate_runtime_config({"inset": -0.1})


def test_validate_runtime_config_rejects_negative_caption_gap():
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_caption_gap_in": -0.1})


def test_validate_runtime_config_accepts_wrap_scalar_shorthand():
    validated = validate_runtime_config({"wrap": 0.2})
    assert validated["wrap"]["top"] == 0.2
    assert validated["wrap"]["right"] == 0.2
    assert validated["wrap"]["bottom"] == 0.2
    assert validated["wrap"]["left"] == 0.2


def test_validate_runtime_config_accepts_wrap_list_shorthand():
    validated = validate_runtime_config({"wrap": [0.1, 0.2, 0.3, 0.4]})
    assert validated["wrap"]["top"] == 0.1
    assert validated["wrap"]["right"] == 0.2
    assert validated["wrap"]["bottom"] == 0.3
    assert validated["wrap"]["left"] == 0.4


def test_validate_runtime_config_accepts_wrap_mapping_shorthand():
    validated = validate_runtime_config({"wrap": {"left": 0.2, "r": 0.3}})
    assert validated["wrap"]["left"] == 0.2
    assert validated["wrap"]["right"] == 0.3
    assert "top" not in validated["wrap"]
    assert "bottom" not in validated["wrap"]


def test_validate_runtime_config_accepts_inset_shorthand():
    validated = validate_runtime_config({"inset": {"t": 0.01, "b": 0.02}})
    assert validated["inset"]["top"] == 0.01
    assert validated["inset"]["bottom"] == 0.02
    assert "left" not in validated["inset"]
    assert "right" not in validated["inset"]


def test_validate_runtime_config_rejects_legacy_flat_side_keys():
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_dist_left_in": 0.2})
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_textbox_inset_top_in": 0.1})


def test_validate_runtime_config_rejects_invalid_shorthand_shapes():
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrap": [0.1, 0.2]})
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrap": {"x": 0.1}})


def test_validate_runtime_config_rejects_negative_shorthand_values():
    with pytest.raises(ValidationError):
        validate_runtime_config({"inset": -0.1})


def test_sidebox_list_and_mapping_inputs_are_equal():
    from_list = SideBox.from_input([1, 1, 1, 1])
    from_mapping = SideBox.from_input({"top": 1, "right": 1, "bottom": 1, "left": 1})
    assert from_list == from_mapping
