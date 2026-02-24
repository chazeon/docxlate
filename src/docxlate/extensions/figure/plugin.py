from __future__ import annotations

from docx.shared import Inches

from docxlate.config_plugins import ExtensionPlugin, register_extension_plugin

from .config import FigureConfig
from .runtime import register as register_runtime


class FigurePlugin(ExtensionPlugin):
    name = "figure"
    config_model = FigureConfig

    def register_runtime(self, latex) -> None:
        register_runtime(latex, plugin=self)

    def figure_config(self, latex) -> dict:
        plugins = latex.context.get("plugins")
        if not isinstance(plugins, dict):
            return {}
        cfg = plugins.get(self.name)
        return cfg if isinstance(cfg, dict) else {}

    def image_wrap_config(self, latex) -> dict:
        figure_cfg = self.figure_config(latex)
        image_cfg = figure_cfg.get("image")
        if not isinstance(image_cfg, dict):
            return {}
        wrap_cfg = image_cfg.get("wrap")
        return wrap_cfg if isinstance(wrap_cfg, dict) else {}

    def caption_gap_emu(self, latex) -> int:
        value = self.image_wrap_config(latex).get("gap")
        if value is None:
            return 114300
        try:
            inches = float(value)
        except (TypeError, ValueError):
            return 114300
        if inches < 0:
            return 114300
        return int(Inches(inches))

    def wrap_offset_y_emu(self, latex) -> int:
        value = None
        shift = self.image_wrap_config(latex).get("shift")
        if isinstance(shift, dict):
            value = shift.get("y")
        if value is None:
            return 0
        try:
            inches = float(value)
        except (TypeError, ValueError):
            return 0
        return int(Inches(inches))


FIGURE_PLUGIN = FigurePlugin()


def register_plugin() -> None:
    register_extension_plugin(FIGURE_PLUGIN)


__all__ = ["FIGURE_PLUGIN", "FigurePlugin", "register_plugin"]
