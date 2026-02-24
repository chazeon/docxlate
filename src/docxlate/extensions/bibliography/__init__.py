from __future__ import annotations

from .plugin import BIBLIOGRAPHY_PLUGIN, register_plugin


def register(latex):
    return BIBLIOGRAPHY_PLUGIN.register_runtime(latex)


__all__ = ["register", "register_plugin"]
