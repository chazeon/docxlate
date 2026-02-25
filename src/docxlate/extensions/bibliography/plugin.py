from __future__ import annotations

from docxlate.config_plugins import ExtensionPlugin, register_extension_plugin

from .config import BibliographyConfig
from .runtime import BIBLIOGRAPHY_MACRO_DEFAULTS, register as register_runtime


class BibliographyPlugin(ExtensionPlugin):
    name = "bibliography"
    config_model = BibliographyConfig

    def register_runtime(self, latex) -> None:
        register_runtime(latex, plugin=self)

    def bibliography_config(self, latex) -> dict:
        plugins = latex.context.get("plugins")
        if not isinstance(plugins, dict):
            return {}
        cfg = plugins.get(self.name)
        return cfg if isinstance(cfg, dict) else {}

    def template(self, latex) -> str | None:
        value = self.bibliography_config(latex).get("template")
        return value if isinstance(value, str) else None

    def et_al_limit(self, latex) -> int:
        value = self.bibliography_config(latex).get("et_al_limit")
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 3
        return parsed if parsed > 0 else 3

    def layout_settings(self, latex) -> dict[str, object]:
        cfg = self.bibliography_config(latex)
        numbering = str(cfg.get("numbering", "bracket")).lower()
        if numbering not in {"bracket", "none"}:
            numbering = "bracket"
        try:
            indent_in = float(cfg.get("indent_in", 0.35))
        except (TypeError, ValueError):
            indent_in = 0.35
        if indent_in <= 0:
            indent_in = 0.35
        return {"numbering": numbering, "indent_in": indent_in}

    def citation_settings(self, latex) -> dict[str, object]:
        cfg = self.bibliography_config(latex)
        compress = bool(cfg.get("citation_compress_ranges", False))
        try:
            min_run = int(cfg.get("citation_range_min_run", 2))
        except (TypeError, ValueError):
            min_run = 2
        if min_run < 2:
            min_run = 2
        return {"compress_ranges": compress, "min_run": min_run}

    def macro_text(self, latex, name: str) -> str:
        cfg = self.bibliography_config(latex)
        overrides = cfg.get("macro_replacements")
        if isinstance(overrides, dict):
            value = overrides.get(name)
            if isinstance(value, str):
                return value
        return BIBLIOGRAPHY_MACRO_DEFAULTS.get(name, "")

    def missing_entry_policy(self, latex) -> str:
        cfg = self.bibliography_config(latex)
        value = str(cfg.get("missing_entry_policy", "key")).lower()
        if value in {"hole", "key"}:
            return value
        return "key"


BIBLIOGRAPHY_PLUGIN = BibliographyPlugin()


def register_plugin() -> None:
    register_extension_plugin(BIBLIOGRAPHY_PLUGIN)


__all__ = ["BIBLIOGRAPHY_PLUGIN", "BibliographyPlugin", "register_plugin"]
