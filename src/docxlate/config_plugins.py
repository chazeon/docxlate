from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel


@dataclass(frozen=True)
class ConfigPlugin:
    model: type[BaseModel]
    apply: Callable[[dict, dict], None]


_PLUGINS: dict[str, ConfigPlugin] = {}


def register_config_plugin(
    name: str, *, model: type[BaseModel], apply: Callable[[dict, dict], None]
) -> None:
    _PLUGINS[name] = ConfigPlugin(model=model, apply=apply)


def get_config_plugin(name: str) -> ConfigPlugin | None:
    return _PLUGINS.get(name)


__all__ = ["ConfigPlugin", "get_config_plugin", "register_config_plugin"]
