from __future__ import annotations

import re
from pathlib import Path

from plasTeX import Command
from plasTeX.TeX import TeX


class newlabel(Command):
    args = 'label data'


class bibcite(Command):
    args = 'key data'


def _fragment_groups(fragment) -> list:
    return [child for child in getattr(fragment, 'childNodes', []) if getattr(child, 'nodeName', None) == 'bgroup']


def _group_text(group) -> str:
    text_content = getattr(group, 'textContent', None)
    if text_content is not None:
        return str(text_content).strip()
    return str(group).strip('{} ')


def parse_refs(fname: str | Path):
    refs: dict[str, dict[str, str | None]] = {}
    bibcites: dict[str, dict[str, str]] = {}

    tex = TeX()
    context = tex.ownerDocument.context
    context.addGlobal('newlabel', newlabel)
    context.addGlobal('bibcite', bibcite)
    tex.input(Path(fname).read_text(encoding='utf-8'))
    doc = tex.parse()

    for node in getattr(doc, 'childNodes', []):
        node_name = getattr(node, 'nodeName', None)
        if node_name == 'newlabel':
            label_value = node.attributes.get('label')
            data_value = node.attributes.get('data')
            if label_value is None or data_value is None:
                continue
            ref_label = str(getattr(label_value, 'textContent', label_value)).strip()
            groups = _fragment_groups(data_value)
            ref_number = _group_text(groups[0]) if groups else None
            refs[ref_label] = {'label': ref_label, 'ref_num': ref_number}
            continue

        if node_name == 'bibcite':
            key_value = node.attributes.get('key')
            data_value = node.attributes.get('data')
            if key_value is None or data_value is None:
                continue
            cite_key = str(getattr(key_value, 'textContent', key_value)).strip()
            groups = _fragment_groups(data_value)
            if not groups:
                continue

            cite_ref_number = _group_text(groups[0]) if len(groups) > 0 else ''
            cite_year = _group_text(groups[1]) if len(groups) > 1 else ''
            cite_authors_short = _group_text(groups[2]) if len(groups) > 2 else ''
            cite_authors_full = _group_text(groups[3]) if len(groups) > 3 else ''

            bibcites[cite_key] = {
                'key': cite_key,
                'ref_num': cite_ref_number,
                'year': cite_year,
                'authors_short': cite_authors_short,
                'authors_full': cite_authors_full,
            }

    return refs, bibcites


def parse_abx_aux_cite_order(fname: str | Path) -> dict[str, int]:
    """
    Parse biblatex aux cite stream and return first-seen citation order.

    Expected form:
      \\abx@aux@cite{<refsection>}{<citekey>}
    """
    cite_order: dict[str, int] = {}
    counter = 1
    pattern = re.compile(r"\\abx@aux@cite\{[^}]*\}\{([^}]+)\}")
    for line in Path(fname).read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if not match:
            continue
        key = match.group(1).strip()
        if not key or key in cite_order:
            continue
        cite_order[key] = counter
        counter += 1
    return cite_order
