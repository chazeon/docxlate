from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config_plugins import get_config_plugin
from .extensions import ensure_config_plugins_registered


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bibliography_template: str | None = None
    bibliography_numbering: Literal["bracket", "none"] | None = None
    bibliography_indent_in: float | None = Field(default=None, gt=0)
    bibliography_et_al_limit: int | None = Field(default=None, gt=0)
    citation_compress_ranges: bool | None = None
    citation_range_min_run: int | None = Field(default=None, gt=1)
    title_render_policy: Literal["explicit", "auto", "always"] | None = None
    parse_skip_packages: list[str] | None = None
    parse_skip_usepackage_paths: list[str] | None = None
    mathml2omml_xsl_path: str | None = None
    plugins: dict[str, Any] | None = None


def validate_runtime_config(data: dict) -> dict:
    ensure_config_plugins_registered()

    validated = RuntimeConfig.model_validate(data)
    dumped = validated.model_dump(exclude_none=True, exclude_unset=True)
    plugin_blocks = dumped.pop("plugins", {}) or {}

    context: dict = dict(dumped)
    for plugin_name, raw_config in plugin_blocks.items():
        plugin = get_config_plugin(plugin_name)
        if plugin is None:
            raise ValueError(
                f"Unknown plugin config namespace: '{plugin_name}'. "
                f"Known plugins must be registered before config validation."
            )
        if not isinstance(raw_config, dict):
            raise ValueError(
                f"Plugin config for '{plugin_name}' must be a mapping/object."
            )
        plugin_values = plugin.model.model_validate(raw_config).model_dump(
            exclude_none=True, exclude_unset=True
        )
        plugin.apply(context, plugin_values)

    return context


__all__ = ["RuntimeConfig", "ValidationError", "validate_runtime_config"]
