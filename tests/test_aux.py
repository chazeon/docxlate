from pathlib import Path
from docxlate.aux import parse_refs


def test_parse_refs_contains_known_label():
    refs, bibcites = parse_refs(Path("tests/fixtures/aux/sample.aux"))
    assert "sec:intro" in refs
    assert str(refs["sec:intro"]["ref_num"]) == "1"
    assert "Foo2025" in bibcites
    assert str(bibcites["Foo2025"]["ref_num"]) == "7"
