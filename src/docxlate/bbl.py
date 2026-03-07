from __future__ import annotations

# Compatibility wrapper; implementation is extension-owned.
from docxlate.extensions.bibliography.artifacts.bbl import (
    DEFAULT_BIB_TEMPLATE,
    BblEntry,
    format_bibliography_entry,
    parse_bbl,
)

__all__ = [
    "BblEntry",
    "DEFAULT_BIB_TEMPLATE",
    "format_bibliography_entry",
    "parse_bbl",
]
