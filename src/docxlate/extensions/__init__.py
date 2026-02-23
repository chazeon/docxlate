from .hyperref import register as register_hyperref_extension
from .figures import register as register_figures_extension
from .lists import register as register_lists_extension

__all__ = [
    "register_hyperref_extension",
    "register_figures_extension",
    "register_lists_extension",
]
