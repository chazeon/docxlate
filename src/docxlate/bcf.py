from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

BCF_NS = {"bcf": "https://sourceforge.net/projects/biblatex"}


def parse_bcf(fname: str | Path) -> dict[str, int]:
    """
    Return the earliest citation order for each cite key declared in a BCF.
    """
    tree = ET.parse(fname)
    root = tree.getroot()
    cite_orders: dict[str, int] = {}

    for section in root.findall(".//bcf:section", BCF_NS):
        for cite in section.findall("bcf:citekey", BCF_NS):
            cite_key = (cite.text or "").strip()
            if not cite_key:
                continue
            order_attr = cite.attrib.get("order")
            if not order_attr:
                continue
            try:
                order_value = int(order_attr)
            except ValueError:
                continue
            if cite_key not in cite_orders:
                cite_orders[cite_key] = order_value

    return cite_orders
