from pathlib import Path
from docxlate.aux import parse_refs


def test_parse_refs_contains_known_label():
    refs, bibcites = parse_refs(Path('main.aux'))
    assert 'fig:overview-framework' in refs
    assert str(refs['fig:overview-framework']['ref_num']) == '1'
    assert bibcites == {}
