# docxlate

**docxlate** is a modern, pragmatic LaTeX to Microsoft Word (`.docx`) converter.

It is designed for workflows where LaTeX run artifacts (like `.aux`, `.bbl`, and `.bcf` files) are essential for maintaining the fidelity of cross-references and citations.

## Key Features

- **High-Fidelity Math**: Uses `latex2mathml` and XSL transforms to produce native Word Equation (OMML) objects.
- **Smart Citations**: Ingests artifacts from real LaTeX/BibLaTeX runs to ensure citation order and bibliography content match your LaTeX project.
- **Floating Figures**: Robust support for `figure` and `wrapfigure` environments with reliable caption placement.
- **Declarative Architecture**: Built on a Flask-style decorator model using `plasTeX` for parsing and `python-docx` for generation.
- **Extensible**: Easily add custom handlers for your own LaTeX macros and environments.

## Quick Start

### Installation

```bash
pip install docxlate
```

### Basic Usage

Convert a LaTeX file to Word:

```bash
docxlate convert input.tex -o output.docx
```

## Navigation

- [Getting Started](01_getting-started.md): Detailed installation and usage instructions.
- [Configuration](02_configuration.md): Learn how to customize the conversion via YAML.
- [Directives](03_directives.md): In-source overrides for specific elements.
- [Features](features/):
    - [Bibliography & Citations](features/bibliography.md)
    - [Figures & Layout](features/figures.md)
    - [Math Conversion](features/math.md)
- [Architecture](04_architecture.md): Deep dive into the internal design.
- [Development](05_development.md): How to run tests and contribute.
