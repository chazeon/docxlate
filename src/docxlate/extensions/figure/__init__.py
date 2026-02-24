from __future__ import annotations

from ..figures import register as register_runtime
from .config import register_plugin


def register(latex):
    return register_runtime(latex)


__all__ = ["register", "register_plugin"]
