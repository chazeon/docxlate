from __future__ import annotations

from .handlers import register_handlers


def register(latex, *, plugin):
    return register_handlers(latex, plugin=plugin)


__all__ = ["register"]
