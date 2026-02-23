# docxlate

LaTeX to Word (`.docx`) converter built on:
- `plasTeX` for parsing/macro expansion
- `python-docx` for document generation

## Status

This project is pragmatic and evolving. It supports many common structures (sections, inline styles, math, citations, references, lists, figures/wrapfigure, links), but is not a full TeX engine.

See `DESIGN.md` for architecture and roadmap.

## Why Not Just Pandoc?

`docxlate` is designed for workflows where LaTeX run artifacts matter.

Unlike a source-only conversion path, `docxlate` can consume files produced by real LaTeX/BibLaTeX runs:
- `.aux` for label/ref and citation-order signals
- `.bbl` for bibliography entry content
- `.bcf` as a fallback citation metadata source

This makes cross-reference and citation behavior closer to the compiled LaTeX project state, especially in documents that depend on multi-pass resolution and bibliography tooling.

## Installation

```bash
pip install .
```

or with `uv`:

```bash
uv sync
```

## CLI

Basic:

```bash
docxlate convert input.tex -o output.docx
```

Use an existing DOCX template:

```bash
docxlate convert input.tex -o output.docx --template template.docx
```

Apply ordered template overrides (later `-t` values override earlier ones):

```bash
docxlate convert input.tex -o output.docx -t base.docx -t styles.xml -t theme1.xml
```

Load runtime config from YAML:

```bash
docxlate convert input.tex -o output.docx --config config.yaml
```

Dump DOCX style/layout parts:

```bash
docxlate dump-styles output.docx -o styles.xml
docxlate dump-theme output.docx -o theme1.xml
docxlate dump-font-table output.docx -o fontTable.xml
```

Dumped XML files are auto-formatted for readability.

If `--config` is omitted, `docxlate.yaml` in the current directory is auto-loaded when present.

Legacy CLI alias `docxlate` is still available for compatibility.

## Library Usage

```python
from docxlate import latex

tex = r"""
\section{Intro}
Hello world.
"""

latex.reset_document()  # optional
latex.context["tex_path"] = "input.tex"  # enables .aux/.bbl lookup conventions
latex.run(tex)
latex.save("output.docx")
```

## Runtime Config (YAML)

Validated with Pydantic (`extra=forbid`). Current keys:

- `bibliography_template`
- `figure_caption_template`
- `bibliography_numbering`: `bracket` | `none`
- `bibliography_indent_in`: float (`> 0`)
- `bibliography_et_al_limit`: int (`> 0`)
- `citation_compress_ranges`: bool
- `citation_range_min_run`: int (`> 1`)
- `title_render_policy`: `explicit` | `auto` | `always`
- `parse_skip_packages`: list of package names to skip in parser input
- `parse_skip_usepackage_paths`: list of `\usepackage{...}` path entries to skip in parser input
- `mathml2omml_xsl_path`: path to MathML->OMML XSL

Example:

```yaml
citation_compress_ranges: true
citation_range_min_run: 2
title_render_policy: explicit
parse_skip_packages:
  - fontspec
  - expl3
mathml2omml_xsl_path: /Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl
figure_caption_template: "\\textbf{<< fig_name >>. << fig_num >>} << caption >>"
```

## Math Conversion

Math uses `latex2mathml` + XSL transform to OMML.

You must provide `mathml2omml_xsl_path` via config/context. If missing, math falls back to raw MathML text and warning.

Note: `mathml2omml.xsl` is commonly available from local Microsoft Office installations; it is not bundled by this project. On macOS, a common path is:

```text
/Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl
```

## Notes on Parsing

- `plasTeX` is not a full TeX layout engine.
- Complex preambles may fail full parse.
- The converter includes body-only fallback and preamble metadata recovery (`\title`, `\author`, `\date`).
- Parser skip lists (`parse_skip_packages`, `parse_skip_usepackage_paths`) help avoid known package failures.

## Testing

```bash
uv run pytest -q
```

(or `pytest tests/`)
