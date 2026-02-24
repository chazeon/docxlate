from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from docxlate.config_plugins import register_config_plugin
from docxlate.model import Edges, Point


class WrapConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pad: Edges | None = None
    inset: Edges | None = None
    gap: float | None = Field(default=None, ge=0)
    shift: Point | None = None

    @field_validator("pad", "inset", mode="before")
    @classmethod
    def _parse_edges(cls, value):
        return Edges.from_input(value)

    @field_validator("shift", mode="before")
    @classmethod
    def _parse_shift(cls, value):
        return Point.from_input(value)


class ImageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["inline", "wrap"] | None = None
    wrap: WrapConfig | None = None


class FigureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption_template: str | None = None
    image: ImageConfig | None = None


def apply_config(context: dict, values: dict) -> None:
    plugins = context.setdefault("plugins", {})
    plugins["figure"] = values


def register_plugin() -> None:
    register_config_plugin(
        "figure",
        model=FigureConfig,
        apply=apply_config,
    )


__all__ = [
    "FigureConfig",
    "ImageConfig",
    "WrapConfig",
    "apply_config",
    "register_plugin",
]
