from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError, field_validator


class Edges(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def _field(long_name: str, short_name: str):
        return Field(
            default=None,
            ge=0,
            validation_alias=AliasChoices(long_name, short_name),
        )

    top: float | None = _field("top", "t")
    right: float | None = _field("right", "r")
    bottom: float | None = _field("bottom", "b")
    left: float | None = _field("left", "l")

    @classmethod
    def from_input(cls, value: Any) -> "Edges | None":
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
            return cls.model_validate(
                {"top": float(t), "right": float(r), "bottom": float(b), "left": float(l)}
            )
        if isinstance(value, dict):
            return cls.model_validate(value)
        raise ValueError("side box value must be a number, 4-number list, or mapping")


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float | None = None
    y: float | None = None

    @classmethod
    def from_input(cls, value: Any) -> "Point | None":
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        if isinstance(value, (int, float)):
            return cls(y=float(value))
        if isinstance(value, (list, tuple)):
            if len(value) != 2:
                raise ValueError("shift list input must contain exactly 2 numbers: [x, y]")
            x, y = value
            return cls(x=float(x), y=float(y))
        if isinstance(value, dict):
            return cls.model_validate(value)
        raise ValueError("shift value must be a number, 2-number list, or mapping")


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
    image: "ImageConfig | None" = None


class ImageWrapConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pad: Edges | None = Field(
        default=None,
        validation_alias=AliasChoices("pad", "wrap"),
    )
    inset: Edges | None = None
    gap: float | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("gap", "gap_in", "caption_gap_in"),
    )
    shift: Point | None = Field(
        default=None,
        validation_alias=AliasChoices("shift", "offset"),
    )

    @field_validator("pad", "inset", mode="before")
    @classmethod
    def _parse_side_box(cls, value):
        return Edges.from_input(value)

    @field_validator("shift", mode="before")
    @classmethod
    def _parse_shift(cls, value):
        return Point.from_input(value)


class ImageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["inline", "wrap"] | None = None
    wrap: ImageWrapConfig | None = None


def validate_runtime_config(data: dict) -> dict:
    validated = RuntimeConfig.model_validate(data)
    return validated.model_dump(exclude_none=True, exclude_unset=True)


__all__ = [
    "RuntimeConfig",
    "Edges",
    "Point",
    "ImageConfig",
    "ImageWrapConfig",
    "ValidationError",
    "validate_runtime_config",
]
