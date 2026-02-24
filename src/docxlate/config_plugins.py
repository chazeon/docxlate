from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ExtensionPlugin(ABC):
    name: str
    config_model: type[BaseModel]

    @abstractmethod
    def register_runtime(self, latex) -> None:
        """Register macros/handlers on a LatexBridge."""

    def apply_config(self, context: dict, values: dict) -> None:
        plugins = context.setdefault("plugins", {})
        plugins[self.name] = values


_PLUGINS: dict[str, ExtensionPlugin] = {}


def register_extension_plugin(plugin: ExtensionPlugin) -> None:
    _PLUGINS[plugin.name] = plugin


def get_extension_plugin(name: str) -> ExtensionPlugin | None:
    return _PLUGINS.get(name)


__all__ = ["ExtensionPlugin", "get_extension_plugin", "register_extension_plugin"]
