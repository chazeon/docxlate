from pathlib import Path

from docxlate.bcf import parse_bcf


def test_bcf_parser_extracts_first_seen_order():
    fixture = Path("tests/fixtures/bcf/sample.bcf")
    orders = parse_bcf(fixture)

    assert orders["Alpha2024"] == 5
    assert orders["Beta2021"] == 2
