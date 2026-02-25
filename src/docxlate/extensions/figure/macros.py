from __future__ import annotations

from plasTeX import Command, Environment


class includegraphics(Command):
    args = "[ options ] file:str"


class caption(Command):
    args = "[ toc ] self"


class wrapfigure(Environment):
    args = "[ lines ] place:str width"


class docxlatefigwrapset(Command):
    args = "path:str value:str"


def register_macros(latex):
    for macro_name, macro_class in {
        "includegraphics": includegraphics,
        "caption": caption,
        "wrapfigure": wrapfigure,
        "docxlatefigwrapset": docxlatefigwrapset,
    }.items():
        latex.macro(macro_name, macro_class)


__all__ = [
    "caption",
    "docxlatefigwrapset",
    "includegraphics",
    "register_macros",
    "wrapfigure",
]
