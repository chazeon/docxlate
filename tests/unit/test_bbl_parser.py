from pathlib import Path

from docxlate.bbl import format_bibliography_entry, parse_bbl


def test_parse_bbl_extracts_entries_and_fields():
    entries = parse_bbl(Path("tests/fixtures/bbl/sample.bbl"))
    assert "KeyA" in entries
    assert "KeyB" in entries

    key_a = entries["KeyA"]
    assert key_a["type"] == "article"
    assert key_a["fields"]["title"] == "A sample article"
    assert key_a["fields"]["pages"] == "10-20"
    assert key_a["fields"]["doi"] == "10.1000/example"
    assert key_a["authors"][:2] == ["Doe, Jane", "Roe, John"]


def test_format_bibliography_entry_contains_core_parts():
    entries = parse_bbl(Path("tests/fixtures/bbl/sample.bbl"))
    formatted = format_bibliography_entry(entries["KeyA"])
    assert "Doe, Jane, Roe, John" in formatted
    assert "(2024)" in formatted
    assert "A sample article" in formatted
    assert r"\textit{J. Testing}" in formatted
    assert "10-20" in formatted
    assert r"\href{https://doi.org/10.1000/example}{10.1000/example}" in formatted


def test_format_bibliography_entry_italicizes_et_al_for_many_authors():
    entry = {
        "authors": ["A, One", "B, Two", "C, Three", "D, Four"],
        "fields": {
            "year": "2025",
            "title": "Sample",
            "journaltitle": "Journal X",
        },
    }
    formatted = format_bibliography_entry(entry)
    assert r"\textit{et al.}" in formatted


def test_format_bibliography_entry_respects_custom_et_al_limit():
    entry = {
        "authors": ["A, One", "B, Two", "C, Three"],
        "fields": {"journaltitle": "Journal X"},
    }
    formatted = format_bibliography_entry(entry, et_al_limit=2)
    assert "A, One, B, Two" in formatted
    assert r"\textit{et al.}" in formatted
    assert "C, Three" not in formatted


def test_format_bibliography_entry_italicizes_journal():
    entry = {
        "authors": ["A, One"],
        "fields": {"journaltitle": "Journal X"},
    }
    formatted = format_bibliography_entry(entry)
    assert r"\textit{Journal X}" in formatted


def test_format_bibliography_entry_supports_custom_template():
    entry = {
        "authors": ["A, One"],
        "fields": {"title": "My Title"},
    }
    formatted = format_bibliography_entry(
        entry,
        template=r"<< authors|join('; ') >> :: << fields.title >>",
    )
    assert formatted == "A, One :: My Title"


def test_format_bibliography_entry_does_not_mutate_doi_hyphens():
    entry = {
        "authors": ["A, One"],
        "fields": {
            "year": "2026",
            "journaltitle": "Journal X",
            "pages": "223-253",
            "doi": "10.1016/0009-2541(94)00140-4",
        },
    }
    formatted = format_bibliography_entry(entry)
    assert "223-253" in formatted
    assert (
        r"\href{https://doi.org/10.1016/0009-2541(94)00140-4}"
        r"{10.1016/0009-2541(94)00140-4}"
    ) in formatted
