from __future__ import annotations

from plasTeX import Command, Environment


class includegraphics(Command):
    args = "[ options ] file:str"


class caption(Command):
    args = "[ toc ] self"


class wrapfigure(Environment):
    args = "[ lines ] place:str width"


def register_macros(latex):
    for macro_name, macro_class in {
        "includegraphics": includegraphics,
        "caption": caption,
        "wrapfigure": wrapfigure,
    }.items():
        latex.macro(macro_name, macro_class)


__all__ = [
    "caption",
    "includegraphics",
    "register_macros",
    "wrapfigure",
]
