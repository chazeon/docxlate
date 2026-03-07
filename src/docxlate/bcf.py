from __future__ import annotations

# Compatibility wrapper; implementation is extension-owned.
from docxlate.extensions.bibliography.artifacts.bcf import (
    declared_fields_from_bcf,
    parse_bcf,
)

__all__ = ["declared_fields_from_bcf", "parse_bcf"]
