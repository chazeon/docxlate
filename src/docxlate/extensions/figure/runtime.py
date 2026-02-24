from __future__ import annotations

from .handlers import register_handlers
from .macros import register_macros


def register(latex, *, plugin):
    register_macros(latex)
    return register_handlers(latex, plugin=plugin)


__all__ = ["register"]
