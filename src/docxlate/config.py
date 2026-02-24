from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bibliography_template: str | None = None
    figure_caption_template: str | None = None
    bibliography_numbering: Literal["bracket", "none"] | None = None
    bibliography_indent_in: float | None = Field(default=None, gt=0)
    bibliography_et_al_limit: int | None = Field(default=None, gt=0)
    citation_compress_ranges: bool | None = None
    citation_range_min_run: int | None = Field(default=None, gt=1)
    title_render_policy: Literal["explicit", "auto", "always"] | None = None
    parse_skip_packages: list[str] | None = None
    parse_skip_usepackage_paths: list[str] | None = None
    mathml2omml_xsl_path: str | None = None
    wrapfigure_dist_left_in: float | None = Field(default=None, ge=0)
    wrapfigure_dist_right_in: float | None = Field(default=None, ge=0)
    wrapfigure_dist_top_in: float | None = Field(default=None, ge=0)
    wrapfigure_dist_bottom_in: float | None = Field(default=None, ge=0)
    wrapfigure_textbox_inset_left_in: float | None = Field(default=None, ge=0)
    wrapfigure_textbox_inset_right_in: float | None = Field(default=None, ge=0)
    wrapfigure_textbox_inset_top_in: float | None = Field(default=None, ge=0)
    wrapfigure_textbox_inset_bottom_in: float | None = Field(default=None, ge=0)
    wrapfigure_caption_gap_in: float | None = Field(default=None, ge=0)


def validate_runtime_config(data: dict) -> dict:
    validated = RuntimeConfig.model_validate(data)
    return validated.model_dump(exclude_none=True, exclude_unset=True)


__all__ = ["RuntimeConfig", "ValidationError", "validate_runtime_config"]
