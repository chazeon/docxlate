from __future__ import annotations

# Compatibility wrapper; implementation is extension-owned.
from docxlate.extensions.bibliography.artifacts.aux import (
    parse_abx_aux_cite_order,
    parse_aux_artifacts,
)
from docxlate.refs import parse_refs

__all__ = ["parse_abx_aux_cite_order", "parse_aux_artifacts", "parse_refs"]
