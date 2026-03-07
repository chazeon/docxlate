from __future__ import annotations

from docxlate.config_plugins import ExtensionPlugin, register_extension_plugin

from .config import TableConfig
from .runtime import register as register_runtime


class TablePlugin(ExtensionPlugin):
    name = "table"
    config_model = TableConfig

    def register_runtime(self, latex) -> None:
        register_runtime(latex, plugin=self)

    def table_config(self, latex) -> dict:
        plugins = latex.context.get("plugins")
        if not isinstance(plugins, dict):
            return {}
        cfg = plugins.get(self.name)
        return cfg if isinstance(cfg, dict) else {}

    def style_candidates(self, latex) -> list[str]:
        cfg = self.table_config(latex)
        raw = cfg.get("style_candidates")
        if isinstance(raw, list):
            parsed = [str(v).strip() for v in raw if str(v).strip()]
            if parsed:
                return parsed
        return ["Table Grid", "TableGrid", "Table Normal", "Normal Table"]

    def fallback_style(self, latex) -> str:
        cfg = self.table_config(latex)
        value = cfg.get("fallback_style")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return "Table Grid"

    def autofit(self, latex) -> bool:
        cfg = self.table_config(latex)
        value = cfg.get("autofit")
        if isinstance(value, bool):
            return value
        return True


TABLE_PLUGIN = TablePlugin()


def register_plugin() -> None:
    register_extension_plugin(TABLE_PLUGIN)


__all__ = ["TABLE_PLUGIN", "TablePlugin", "register_plugin"]
