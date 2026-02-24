from __future__ import annotations


def trim_trailing_whitespace_runs(paragraph):
    # Remove trailing whitespace-only text runs on anchor host paragraphs.
    while paragraph.runs:
        run = paragraph.runs[-1]
        text = run.text or ""
        if not text or not text.isspace():
            break
        run._r.getparent().remove(run._r)


__all__ = ["trim_trailing_whitespace_runs"]
