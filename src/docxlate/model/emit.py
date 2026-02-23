from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StyleState:
    theme: str = "minor"
    bold: bool = False
    italic: bool = False
    small_caps: bool = False
    monospace: bool = False
    color: str | None = None


@dataclass
class LinkTarget:
    anchor: str | None = None
    url: str | None = None
    rel_id: str | None = None

    @classmethod
    def from_value(cls, value) -> "LinkTarget | None":
        if not value:
            return None
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            return None
        return cls(anchor=value.get("anchor"), url=value.get("url"), rel_id=value.get("rel_id"))


@dataclass(frozen=True)
class TextSpan:
    text: str
    style: StyleState
    char_role: str | None = None


@dataclass(frozen=True)
class EquationSpec:
    latex: str
    number: str | None = None
    color: str | None = None
    display: bool = True
