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


def figure_macro_classes() -> dict[str, type[Command] | type[Environment]]:
    return {
        "includegraphics": includegraphics,
        "caption": caption,
        "wrapfigure": wrapfigure,
        "docxlatefigwrapset": docxlatefigwrapset,
    }


def register_macros(latex):
    for macro_name, macro_class in figure_macro_classes().items():
        latex.macro(macro_name, macro_class)


__all__ = [
    "caption",
    "docxlatefigwrapset",
    "figure_macro_classes",
    "includegraphics",
    "register_macros",
    "wrapfigure",
]
