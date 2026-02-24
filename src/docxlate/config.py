from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class SideBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top: float | None = Field(default=None, ge=0)
    right: float | None = Field(default=None, ge=0)
    bottom: float | None = Field(default=None, ge=0)
    left: float | None = Field(default=None, ge=0)

    @classmethod
    def from_input(cls, value: Any) -> "SideBox | None":
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        if isinstance(value, (int, float)):
            number = float(value)
            return cls(top=number, right=number, bottom=number, left=number)
        if isinstance(value, (list, tuple)):
            if len(value) != 4:
                raise ValueError("side box list input must contain exactly 4 numbers")
            t, r, b, l = value
            return cls(top=float(t), right=float(r), bottom=float(b), left=float(l))
        if isinstance(value, dict):
            data = dict(value)
            aliases = {
                "t": "top",
                "r": "right",
                "b": "bottom",
                "l": "left",
            }
            normalized = {}
            for key, raw in data.items():
                resolved = aliases.get(str(key), str(key))
                if resolved not in {"top", "right", "bottom", "left"}:
                    raise ValueError(f"unsupported side key: {key}")
                normalized[resolved] = float(raw)
            return cls(**normalized)
        raise ValueError("side box value must be a number, 4-number list, or mapping")


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
    wrap: SideBox | None = None
    inset: SideBox | None = None
    wrapfigure_caption_gap_in: float | None = Field(default=None, ge=0)

    @field_validator("wrap", "inset", mode="before")
    @classmethod
    def _parse_side_box(cls, value):
        return SideBox.from_input(value)


def validate_runtime_config(data: dict) -> dict:
    validated = RuntimeConfig.model_validate(data)
    return validated.model_dump(exclude_none=True, exclude_unset=True)


__all__ = ["RuntimeConfig", "SideBox", "ValidationError", "validate_runtime_config"]
