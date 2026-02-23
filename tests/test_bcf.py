from pathlib import Path
from docxlate.bcf import parse_bcf


def test_parse_bcf_returns_first_order():
    orders = parse_bcf(Path('main.bcf'))
    assert orders['McDonough1995'] == 1
    assert orders['Tromp2004'] == 3
