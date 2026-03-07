from .bibliography import register as register_bibliography_extension
from .hyperref import register as register_hyperref_extension
from .figure import register as register_figures_extension
from .lists import register as register_lists_extension
from .table import register as register_table_extension
from .xcolor import register as register_xcolor_extension


def ensure_config_plugins_registered():
    # Import-time registration for built-in extension-owned config models.
    from .bibliography import register_plugin as register_bibliography_plugin
    from .figure import register_plugin as register_figure_plugin
    from .table import register_plugin as register_table_plugin

    register_bibliography_plugin()
    register_figure_plugin()
    register_table_plugin()


__all__ = [
    "register_bibliography_extension",
    "register_hyperref_extension",
    "register_figures_extension",
    "register_lists_extension",
    "register_table_extension",
    "register_xcolor_extension",
    "ensure_config_plugins_registered",
]
