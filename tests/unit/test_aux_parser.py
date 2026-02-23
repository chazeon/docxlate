from pathlib import Path

from docxlate.aux import parse_refs


def test_aux_parser_extracts_labels_and_citations():
    fixture = Path("tests/fixtures/aux/sample.aux")
    refs, bibcites = parse_refs(fixture)

    assert refs["sec:intro"]["ref_num"] == "1"
    assert refs["eq:energy"]["ref_num"] == "2"
    assert bibcites["Foo2025"]["ref_num"] == "7"
    assert bibcites["Foo2025"]["year"] == "2025"
