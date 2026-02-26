from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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
                raise ValueError("edge list input must contain exactly 4 numbers")
            t, r, b, l = value
            return cls.model_validate(
                {"top": float(t), "right": float(r), "bottom": float(b), "left": float(l)}
            )
        if isinstance(value, dict):
            return cls.model_validate(value)
        raise ValueError("edge value must be a number, 4-number list, or mapping")


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


__all__ = ["Edges", "Point"]
