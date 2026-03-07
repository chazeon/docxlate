import pytest
from pydantic import ValidationError

from docxlate.config import validate_runtime_config
from docxlate.model import Edges, Point


def test_validate_runtime_config_accepts_core_and_figure_plugin_fields():
    data = {
        "title_render_policy": "auto",
        "parse_skip_packages": ["fontspec"],
        "parse_skip_usepackage_paths": ["styles/proposal-compact"],
        "mathml2omml_xsl_path": "/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL",
        "unknown_macro_policy": "warn",
        "unknown_macro_allowlist": ["newcommand", "providecommand"],
        "plugins": {
            "bibliography": {
                "template": "<< fields.title >>",
                "numbering": "none",
                "indent_in": 0.4,
                "et_al_limit": 2,
                "macro_replacements": {"bibinitperiod": "·"},
                "citation_compress_ranges": True,
                "citation_range_min_run": 3,
                "missing_entry_policy": "hole",
            },
            "figure": {
                "caption": {"template": r"\textbf{Figure. << x >>} << caption >>"},
                "image": {
                    "kind": "wrap",
                    "wrap": {
                        "pad": [0.05, 0.3, 0.06, 0.2],
                        "inset": {"left": 0.01, "right": 0.02, "top": 0.03, "bottom": 0.04},
                        "gap": 0.2,
                        "shift": {"y": 0.1},
                    },
                },
            },
            "table": {
                "style_candidates": ["GridTable4", "Table Grid"],
                "fallback_style": "Table Grid",
                "autofit": False,
                "header": {"first_row_bold": True},
            },
        },
    }
    validated = validate_runtime_config(data)
    assert validated["plugins"]["bibliography"]["template"] == "<< fields.title >>"
    assert validated["plugins"]["bibliography"]["numbering"] == "none"
    assert validated["plugins"]["bibliography"]["indent_in"] == 0.4
    assert validated["plugins"]["bibliography"]["et_al_limit"] == 2
    assert validated["plugins"]["bibliography"]["macro_replacements"]["bibinitperiod"] == "·"
    assert validated["plugins"]["bibliography"]["citation_compress_ranges"] is True
    assert validated["plugins"]["bibliography"]["citation_range_min_run"] == 3
    assert validated["plugins"]["bibliography"]["missing_entry_policy"] == "hole"
    assert validated["title_render_policy"] == "auto"
    assert validated["parse_skip_packages"] == ["fontspec"]
    assert validated["parse_skip_usepackage_paths"] == ["styles/proposal-compact"]
    assert validated["mathml2omml_xsl_path"] == "/Applications/Microsoft Word.app/Contents/Resources/MML2OMML.XSL"
    assert validated["unknown_macro_policy"] == "warn"
    assert validated["unknown_macro_allowlist"] == ["newcommand", "providecommand"]
    assert validated["plugins"]["figure"]["caption"]["template"] == r"\textbf{Figure. << x >>} << caption >>"
    assert validated["plugins"]["figure"]["image"]["kind"] == "wrap"
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["left"] == 0.2
    assert validated["plugins"]["figure"]["image"]["wrap"]["inset"]["right"] == 0.02
    assert validated["plugins"]["figure"]["image"]["wrap"]["gap"] == 0.2
    assert validated["plugins"]["figure"]["image"]["wrap"]["shift"]["y"] == 0.1
    assert validated["plugins"]["table"]["style_candidates"] == ["GridTable4", "Table Grid"]
    assert validated["plugins"]["table"]["fallback_style"] == "Table Grid"
    assert validated["plugins"]["table"]["autofit"] is False
    assert validated["plugins"]["table"]["header"]["first_row_bold"] is True


def test_validate_runtime_config_accepts_wrap_caption_anchor_mode():
    validated = validate_runtime_config(
        {"plugins": {"figure": {"image": {"wrap": {"caption_anchor": "separate"}}}}}
    )
    assert validated["plugins"]["figure"]["image"]["wrap"]["caption_anchor"] == "separate"


def test_validate_runtime_config_rejects_invalid_wrap_caption_anchor_mode():
    with pytest.raises(ValidationError):
        validate_runtime_config(
            {"plugins": {"figure": {"image": {"wrap": {"caption_anchor": "split"}}}}}
        )


def test_validate_runtime_config_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        validate_runtime_config({"unknown_option": 1})


def test_validate_runtime_config_rejects_unknown_plugin_namespace():
    with pytest.raises(ValueError):
        validate_runtime_config({"plugins": {"unknown": {}}})


def test_validate_runtime_config_rejects_non_mapping_plugin_block():
    with pytest.raises(ValueError):
        validate_runtime_config({"plugins": {"figure": 123}})


def test_validate_runtime_config_rejects_unknown_table_plugin_key():
    with pytest.raises(ValueError) as exc_info:
        validate_runtime_config({"plugins": {"table": {"unknown_field": True}}})
    assert "plugins.table.unknown_field: Extra inputs are not permitted" in str(exc_info.value)


def test_validate_runtime_config_unknown_plugin_key_shows_available_keys():
    with pytest.raises(ValueError) as exc_info:
        validate_runtime_config({"plugins": {"figure": {"unknown_field": 1}}})
    message = str(exc_info.value)
    assert "plugins.figure.unknown_field: Extra inputs are not permitted" in message
    assert "Available keys: caption, image" in message


def test_validate_runtime_config_rejects_non_positive_indent():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"bibliography": {"indent_in": 0}}})


def test_validate_runtime_config_rejects_non_positive_et_al_limit():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"bibliography": {"et_al_limit": 0}}})


def test_validate_runtime_config_rejects_non_string_bibliography_macro_replacement():
    with pytest.raises(ValidationError):
        validate_runtime_config(
            {"plugins": {"bibliography": {"macro_replacements": {"bibinitperiod": 1}}}}
        )


def test_validate_runtime_config_rejects_small_citation_min_run():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"bibliography": {"citation_range_min_run": 1}}})


def test_validate_runtime_config_rejects_omit_missing_entry_policy():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"bibliography": {"missing_entry_policy": "omit"}}})


def test_validate_runtime_config_rejects_invalid_title_policy():
    with pytest.raises(ValidationError):
        validate_runtime_config({"title_render_policy": "sometimes"})


def test_validate_runtime_config_rejects_invalid_unknown_macro_policy():
    with pytest.raises(ValidationError):
        validate_runtime_config({"unknown_macro_policy": "allow"})


def test_validate_runtime_config_rejects_negative_wrap_distances():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"figure": {"image": {"wrap": {"pad": -0.1}}}}})


def test_validate_runtime_config_rejects_negative_textbox_insets():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"figure": {"image": {"wrap": {"inset": -0.1}}}}})


def test_validate_runtime_config_rejects_negative_caption_gap():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"figure": {"image": {"wrap": {"gap": -0.1}}}}})


def test_validate_runtime_config_accepts_wrap_scalar_shorthand():
    validated = validate_runtime_config({"plugins": {"figure": {"image": {"wrap": {"pad": 0.2}}}}})
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["top"] == 0.2
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["right"] == 0.2
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["bottom"] == 0.2
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["left"] == 0.2


def test_validate_runtime_config_accepts_wrap_list_shorthand():
    validated = validate_runtime_config(
        {"plugins": {"figure": {"image": {"wrap": {"pad": [0.1, 0.2, 0.3, 0.4]}}}}}
    )
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["top"] == 0.1
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["right"] == 0.2
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["bottom"] == 0.3
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["left"] == 0.4


def test_validate_runtime_config_accepts_wrap_mapping_shorthand():
    validated = validate_runtime_config(
        {"plugins": {"figure": {"image": {"wrap": {"pad": {"left": 0.2, "r": 0.3}}}}}}
    )
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["left"] == 0.2
    assert validated["plugins"]["figure"]["image"]["wrap"]["pad"]["right"] == 0.3
    assert "top" not in validated["plugins"]["figure"]["image"]["wrap"]["pad"]
    assert "bottom" not in validated["plugins"]["figure"]["image"]["wrap"]["pad"]


def test_validate_runtime_config_accepts_inset_shorthand():
    validated = validate_runtime_config(
        {"plugins": {"figure": {"image": {"wrap": {"inset": {"t": 0.01, "b": 0.02}}}}}}
    )
    assert validated["plugins"]["figure"]["image"]["wrap"]["inset"]["top"] == 0.01
    assert validated["plugins"]["figure"]["image"]["wrap"]["inset"]["bottom"] == 0.02
    assert "left" not in validated["plugins"]["figure"]["image"]["wrap"]["inset"]
    assert "right" not in validated["plugins"]["figure"]["image"]["wrap"]["inset"]


def test_validate_runtime_config_rejects_legacy_flat_side_keys():
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_dist_left_in": 0.2})
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrapfigure_textbox_inset_top_in": 0.1})
    with pytest.raises(ValidationError):
        validate_runtime_config({"wrap": 0.1})
    with pytest.raises(ValidationError):
        validate_runtime_config({"inset": 0.1})


def test_validate_runtime_config_rejects_invalid_shorthand_shapes():
    with pytest.raises(ValidationError):
        validate_runtime_config(
            {"plugins": {"figure": {"image": {"wrap": {"pad": [0.1, 0.2]}}}}}
        )
    with pytest.raises(ValueError):
        validate_runtime_config(
            {"plugins": {"figure": {"image": {"wrap": {"pad": {"x": 0.1}}}}}}
        )


def test_validate_runtime_config_rejects_negative_shorthand_values():
    with pytest.raises(ValidationError):
        validate_runtime_config({"plugins": {"figure": {"image": {"wrap": {"inset": -0.1}}}}})


def test_validate_runtime_config_accepts_shift_scalar_and_mapping():
    v1 = validate_runtime_config({"plugins": {"figure": {"image": {"wrap": {"shift": 0.25}}}}})
    v2 = validate_runtime_config(
        {"plugins": {"figure": {"image": {"wrap": {"shift": {"y": 0.25}}}}}}
    )
    assert v1["plugins"]["figure"]["image"]["wrap"]["shift"]["y"] == 0.25
    assert v2["plugins"]["figure"]["image"]["wrap"]["shift"]["y"] == 0.25


def test_validate_runtime_config_accepts_shift_xy_list():
    v = validate_runtime_config({"plugins": {"figure": {"image": {"wrap": {"shift": [0.1, 0.2]}}}}})
    assert v["plugins"]["figure"]["image"]["wrap"]["shift"]["x"] == 0.1
    assert v["plugins"]["figure"]["image"]["wrap"]["shift"]["y"] == 0.2


def test_validate_runtime_config_rejects_invalid_shift_mapping():
    with pytest.raises(ValueError):
        validate_runtime_config(
            {"plugins": {"figure": {"image": {"wrap": {"shift": {"z": 0.1}}}}}}
        )
    with pytest.raises(ValidationError):
        validate_runtime_config(
            {"plugins": {"figure": {"image": {"wrap": {"shift": [0.1]}}}}}
        )


def test_edges_list_and_mapping_inputs_are_equal():
    from_list = Edges.from_input([1, 1, 1, 1])
    from_mapping = Edges.from_input({"top": 1, "right": 1, "bottom": 1, "left": 1})
    assert from_list == from_mapping


def test_point_scalar_and_mapping_inputs_are_equal():
    from_scalar = Point.from_input(0.5)
    from_mapping = Point.from_input({"y": 0.5})
    assert from_scalar == from_mapping
