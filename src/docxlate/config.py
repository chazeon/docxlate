from __future__ import annotations

from typing import Any, Literal, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config_plugins import get_extension_plugin, list_extension_plugin_names
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


def _unwrap_model(annotation: Any) -> type[BaseModel] | None:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    origin = get_origin(annotation)
    if origin is None:
        return None
    for arg in get_args(annotation):
        unwrapped = _unwrap_model(arg)
        if unwrapped is not None:
            return unwrapped
    return None


def _model_at_path(root_model: type[BaseModel], path: tuple[Any, ...]) -> type[BaseModel] | None:
    model: type[BaseModel] | None = root_model
    for segment in path:
        if model is None or not isinstance(segment, str):
            return None
        field = model.model_fields.get(segment)
        if field is None:
            return None
        model = _unwrap_model(field.annotation)
    return model


def _available_keys_text(
    *,
    root_model: type[BaseModel],
    loc: tuple[Any, ...],
    plugin_names: list[str],
) -> str | None:
    parent_model = _model_at_path(root_model, tuple(loc[:-1]))
    if parent_model is not None:
        keys = sorted(parent_model.model_fields.keys())
        return ", ".join(keys)
    if len(loc) == 1:
        keys = sorted(root_model.model_fields.keys())
        if plugin_names:
            keys.append(f"plugins.<{'|'.join(plugin_names)}>")
        return ", ".join(keys)
    return None


def _format_validation_errors(
    exc: ValidationError,
    *,
    root_model: type[BaseModel],
    plugin_names: list[str],
    prefix: tuple[Any, ...] = (),
) -> str:
    lines: list[str] = []
    for item in exc.errors():
        loc = tuple(prefix) + tuple(item.get("loc", ()))
        loc_path = ".".join(str(part) for part in loc) if loc else "<root>"
        msg = item.get("msg", "invalid value")
        line = f"{loc_path}: {msg}"
        if item.get("type") == "extra_forbidden":
            available = _available_keys_text(
                root_model=root_model,
                loc=tuple(item.get("loc", ())),
                plugin_names=plugin_names,
            )
            if available:
                line += f". Available keys: {available}"
        lines.append(line)
    return "Configuration validation failed:\n- " + "\n- ".join(lines)


def format_runtime_config_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return _format_validation_errors(
            exc,
            root_model=RuntimeConfig,
            plugin_names=list_extension_plugin_names(),
        )
    return str(exc)


def validate_runtime_config(data: dict) -> dict:
    ensure_config_plugins_registered()

    validated = RuntimeConfig.model_validate(data)
    dumped = validated.model_dump(exclude_none=True, exclude_unset=True)
    plugin_blocks = dumped.pop("plugins", {}) or {}

    context: dict = dict(dumped)
    for plugin_name, raw_config in plugin_blocks.items():
        plugin = get_extension_plugin(plugin_name)
        if plugin is None:
            raise ValueError(
                f"Unknown plugin config namespace: '{plugin_name}'. "
                f"Known plugins must be registered before config validation."
            )
        if not isinstance(raw_config, dict):
            raise ValueError(
                f"Plugin config for '{plugin_name}' must be a mapping/object."
            )
        try:
            plugin_values = plugin.config_model.model_validate(raw_config).model_dump(
                exclude_none=True, exclude_unset=True
            )
        except ValidationError as exc:
            has_unknown = any(item.get("type") == "extra_forbidden" for item in exc.errors())
            if has_unknown:
                raise ValueError(
                    _format_validation_errors(
                        exc,
                        root_model=plugin.config_model,
                        plugin_names=[],
                        prefix=("plugins", plugin_name),
                    )
                ) from exc
            raise
        plugin.apply_config(context, plugin_values)

    return context


__all__ = [
    "RuntimeConfig",
    "ValidationError",
    "format_runtime_config_error",
    "validate_runtime_config",
]
