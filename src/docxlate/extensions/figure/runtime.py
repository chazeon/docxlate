from __future__ import annotations

from .handlers import register_handlers

FIGURE_WRAP_DIRECTIVE_PATH_PATTERN = (
    r"figure\.wrap\.(?:shift\.[xy]|gap|pad\.(?:left|right|top|bottom)|inset\.(?:left|right|top|bottom))"
)


def register(latex, *, plugin):
    latex.register_comment_directive(
        path_pattern=FIGURE_WRAP_DIRECTIVE_PATH_PATTERN,
        macro_name="docxlatefigwrapset",
    )
    return register_handlers(latex, plugin=plugin)


__all__ = ["FIGURE_WRAP_DIRECTIVE_PATH_PATTERN", "register"]
