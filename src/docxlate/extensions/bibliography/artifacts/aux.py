from __future__ import annotations

import re
from pathlib import Path

from docxlate.refs import parse_refs, parse_refs_text


def _parse_abx_aux_cite_order_from_text(aux_text: str) -> dict[str, int]:
    """
    Parse biblatex aux cite stream and return first-seen citation order.

    Expected form:
      \\abx@aux@cite{<refsection>}{<citekey>}
    """
    cite_order: dict[str, int] = {}
    counter = 1
    pattern = re.compile(r"\\abx@aux@cite\{[^}]*\}\{([^}]+)\}")
    for line in aux_text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        key = match.group(1).strip()
        if not key or key in cite_order:
            continue
        cite_order[key] = counter
        counter += 1
    return cite_order


def parse_aux_artifacts(fname: str | Path) -> tuple[
    dict[str, dict[str, str | None]],
    dict[str, dict[str, str]],
    dict[str, int],
]:
    aux_text = Path(fname).read_text(encoding="utf-8")
    refs, bibcites = parse_refs_text(aux_text)
    cite_order = _parse_abx_aux_cite_order_from_text(aux_text)
    return refs, bibcites, cite_order


def parse_abx_aux_cite_order(fname: str | Path) -> dict[str, int]:
    _refs, _bibcites, cite_order = parse_aux_artifacts(fname)
    return cite_order


__all__ = ["parse_abx_aux_cite_order", "parse_aux_artifacts", "parse_refs"]
