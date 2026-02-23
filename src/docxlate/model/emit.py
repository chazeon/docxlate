from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StyleState:
    theme: str = "minor"
    bold: bool = False
    italic: bool = False
    small_caps: bool = False
    monospace: bool = False


@dataclass
class LinkTarget:
    anchor: str | None = None
    url: str | None = None
    rel_id: str | None = None


@dataclass(frozen=True)
class TextSpan:
    text: str
    style: StyleState
    char_role: str | None = None


@dataclass(frozen=True)
class EquationSpec:
    latex: str
    number: str | None = None
