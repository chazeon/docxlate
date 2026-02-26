# Getting Started

## Installation

### From PyPI

```bash
pip install docxlate
```

### From Source

If you want to contribute or use the latest development version:

```bash
git clone https://github.com/chazeon/latex2docx.git
cd latex2docx
pip install .
```

Or using `uv`:

```bash
uv sync
```

## CLI Usage

The primary way to use `docxlate` is via the command line.

### Basic Conversion

```bash
docxlate convert input.tex -o output.docx
```

### Using Templates

You can use an existing `.docx` file as a template to preserve styles, headers, and footers:

```bash
docxlate convert input.tex -o output.docx --template template.docx
```

You can also apply multiple style/theme overrides:

```bash
docxlate convert input.tex -o output.docx -t base.docx -t styles.xml -t theme1.xml
```

### Inspecting DOCX Parts

`docxlate` provides tools to dump internal XML parts of a Word document, which can be useful for creating your own style overrides:

```bash
docxlate dump-styles output.docx -o styles.xml
docxlate dump-theme output.docx -o theme1.xml
docxlate dump-font-table output.docx -o fontTable.xml
```

## Library Usage

You can also use `docxlate` as a Python library.

```python
from docxlate import latex

tex = r"""
\section{Introduction}
This is a \textbf{LaTeX} document converted to Word.
"""

# Enables .aux/.bbl lookup conventions if your TeX file is on disk
latex.context["tex_path"] = "path/to/your/input.tex"

latex.run(tex)
latex.save("output.docx")
```

## Math Requirements

For math conversion to work correctly, `docxlate` requires a MathML to OMML XSL transform file. This is usually bundled with Microsoft Word.

On macOS, it's typically located at:
`/Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl`

You should specify this path in your [configuration](02_configuration.md).
