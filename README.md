# docxlate

LaTeX to Word (`.docx`) converter built on:
- `plasTeX` for parsing/macro expansion
- `python-docx` for document generation

## Status

This project is pragmatic and evolving. It supports many common structures (sections, inline styles, math, citations, references, lists, figures/wrapfigure, links), but is not a full TeX engine.

See the [Documentation](docs/00_index.md) for full details on architecture, features, and configuration.

## Why Not Just Pandoc?

`docxlate` is designed for workflows where LaTeX run artifacts matter.

Unlike a source-only conversion path, `docxlate` can consume files produced by real LaTeX/BibLaTeX runs:
- `.aux` for label/ref and citation-order signals
- `.bbl` for bibliography entry content
- `.bcf` as a fallback citation metadata source

This makes cross-reference and citation behavior closer to the compiled LaTeX project state, especially in documents that depend on multi-pass resolution and bibliography tooling.

## Installation

```bash
pip install docxlate
```

or with `uv`:

```bash
uv sync
```

## CLI

Main command:

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

If `--config` is omitted, `docxlate.yaml` in the current directory is auto-loaded when present.

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

Configuration uses a modular plugin system. Detailed documentation is available in [docs/02_configuration.md](docs/02_configuration.md).

Example `docxlate.yaml`:

```yaml
title_render_policy: explicit
parse_skip_packages:
  - fontspec
  - expl3
mathml2omml_xsl_path: /Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl

plugins:
  bibliography:
    citation_compress_ranges: true
    citation_range_min_run: 2
  figure:
    caption:
      template: "\\textbf{<< fig_name >>. << fig_num >>} << caption >>"
```

## Per-Figure Comment Directives

For one-off overrides of floating figure placement, you can add inline directives in LaTeX comments. See [docs/03_directives.md](docs/03_directives.md) for the full list of supported keys.

Example:

```tex
\begin{wrapfigure}{r}{0.4\textwidth}
% docxlate: figure.wrap.shift.y=0.2
% docxlate: figure.wrap.pad.left=0.2
% docxlate: figure.wrap.gap=0.2
\includegraphics{fig.png}
\caption{Shifted down by 0.2in}
\end{wrapfigure}
```

## Math Conversion

Math uses `latex2mathml` + XSL transform to OMML. You must provide `mathml2omml_xsl_path` via config. See [docs/features/02_math.md](docs/features/math.md) for more info.

## Testing

```bash
uv run pytest
```
