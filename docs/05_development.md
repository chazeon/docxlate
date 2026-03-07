# Development

## Setup

The project uses `uv` for dependency management.

```bash
git clone https://github.com/chazeon/latex2docx.git
cd latex2docx
uv sync
```

## Running Tests

We use `pytest` for testing.

```bash
uv run pytest
```

### Test Structure

- `tests/unit/`: Unit tests for individual components (parsers, utilities).
- `tests/integration/`: High-level tests that verify end-to-end conversion.
- `tests/regression/`: Tests for previously fixed bugs.
- `tests/fixtures/`: LaTeX, AUX, BBL, and BCF files used for testing.

## Architecture Guardrails (Required)

- **Macro registration**: Use `MacroSpec`-backed registration for commands/environments.
- **Decorator strictness**: decorator registration without `parse_class` is disallowed by default (`LatexBridge(strict_macro_specs=True)`).
  - Compatibility fallback exists only as an explicit opt-in (`LatexBridge(strict_macro_specs=False)`).
- **Core boundary**: avoid adding feature-specific policy to `LatexBridge`; place feature behavior in extensions.
- **Artifact ownership**: bibliography artifact processing (`.aux`/`.bbl`/`.bcf`) should be extension-owned and loaded once per run.

### Core Parse-Class Mapping (Current)

- Core handlers in `src/docxlate/handlers.py` are registered with explicit parse classes:
  - sectioning: `section`, `subsection`, `subsubsection`, `paragraph`
  - front matter: `title`, `author`, `date`, `maketitle`
  - paragraph controls: `noindent`, `indent`, `Needspace`
  - inline math: `$`, `math`
  - block math: `equation`

## CI Expectations

- Registry integrity tests must pass (no parser/renderer drift).
- New feature work should not introduce direct `latex.macro(...)` legacy wiring for runtime macros.
- Unknown command/environment behavior must follow documented allowlist policy; do not add silent fallback paths.
  - Runtime policy keys: `unknown_macro_policy` (`warn` or `strict`) and `unknown_macro_allowlist` (list of macro names).
  - In `warn` mode, keep inner content visible and emit warnings; in `strict`, fail on first unknown macro.
- When touching migration areas, run targeted suites:
  - `tests/unit/test_registry.py`
  - `tests/integration/test_style_scope.py`
  - `tests/integration/test_references.py`
  - `tests/integration/test_citations.py`

## Behavioral Specification (Golden Cases)

To ensure the technical integrity of the converter, all changes must adhere to the following behavioral standards. These cases serve as the "Functional Specification" for the project.

### 1. Structure & Semantic Mapping
- **Sections**: `\\section{Intro}` must map to the Word `Heading 1` style with the exact text "Intro".
- **Lists**: Nested `itemize` or `enumerate` environments must preserve correct indentation and bullet/number levels in Word.
- **Tables**: Table rendering must prioritize template-defined table styles (e.g., `Table Grid`) and fall back to deterministic defaults for borders and alignment.

### 2. Formatting & Styles
- **Inline Nesting**: `\\textbf{\\emph{text}}` must be rendered as a single Word Run that is both bold and italic.
- **Declarations**: `{\\bfseries Bold} Normal` must correctly transition from bold to normal text at the group boundary.
- **Color**: Colors specified via `\\color{...}` must be applied directly to the text runs and propagated correctly into math blocks.

### 3. Math & Equations
- **High-Fidelity Math**: Valid math must produce native Word Equation (OMML) objects.
- **Equation Numbering**: `\\eqref{eq:x}` must render the resolved number inside parentheses (e.g., `(1.2)`), regardless of the raw artifact string.
- **Fallback**: If math conversion fails, the raw LaTeX source must be rendered as plain text to prevent data loss.

### 4. Citations & References
- **Range Compression**: Consecutive numeric citations (e.g., `\\cite{A,B,C,D,E}`) must compress to ranges (e.g., `[1–5]`) according to the style configuration.
- **Hyperlinks**: Citations and internal references (`\\ref`) must be converted into clickable internal hyperlinks in the DOCX file.
- **Bibliography**: Bibliography entries must match the formatted content in the `.bbl` file exactly, ensuring parity with the LaTeX run.

### 5. Figures & Floats
- **Caption Linking**: Figure captions must be correctly associated with their corresponding figure labels in the Word anchor system.
- **Wrapfigure**: Wrapped figures must maintain their alignment (left/right) and respect both global padding and per-figure [Directives](03_directives.md).
- **Graceful Degradation**: If an image asset is missing, the converter must still render the caption and a placeholder box to maintain document structure.

## Contributing

1.  **Issue**: Check the issue tracker for existing bugs or feature requests.
2.  **Branch**: Create a new branch for your changes.
3.  **Test**: Add a test case for your changes. If you're fixing a bug, add a regression test.
4.  **Lint**: Ensure your code follows the project's style (we recommend using `ruff`).
5.  **Pull Request**: Submit a PR with a clear description of your changes.

## Roadmap

See the `DESIGN.md` file in the root directory for the long-term project goals and upcoming features.
