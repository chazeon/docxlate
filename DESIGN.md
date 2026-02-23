# Design Document: docxlate

## Overview
`docxlate` is a Python library that converts LaTeX documents into Microsoft Word (`.docx`) files using a declarative, Flask-style decorator model. It uses `plasTeX` for LaTeX parsing/macro expansion and `python-docx` for document generation.

## Goals
- Convert common LaTeX structures into semantically correct Word content.
- Provide an extensible handler system for commands and environments.
- Preserve a clean visitor/decorator authoring interface for users.
- Support robust cross-references (`\label`, `\ref`, `\eqref`, citation links).
- Support citation formatting behaviors (numeric ranges like `[1-5]`, style-aware rendering).
- Handle floating content (`figure`, `wrapfigure`) with reliable caption rendering.
- Produce professional default output compatible with Word themes/templates.
- Fail gracefully when unsupported LaTeX features are encountered.

## Non-Goals (initial phase)
- Full TeX engine parity.
- Perfect visual fidelity for all packages and custom macros.
- Supporting every LaTeX package out of the box.

## Architecture

### 1. Core Engine (`LatexBridge`)
Central conversion class.
- **Registry**: Maps LaTeX commands/environments to handlers.
- **Document state**: Owns a `python-docx` `Document` plus conversion context.
- **Visitor dispatch**: Recursively traverses the parsed AST and dispatches handlers.
- **Diagnostics**: Records warnings/errors with source context when possible.

### 2. Handler Layer
Handlers are user-defined (or default) functions registered with `@latex.tag` and `@latex.env`.
- **Command handlers**: e.g., `\section`, `\textbf`, `\emph`, `\href`.
- **Environment handlers**: e.g., `equation`, `itemize`, `enumerate`, `figure`.
- **Lifecycle hooks/events**: pre-parse, pre-render, post-render.
- **Fallback handler**: called for unsupported commands/environments.

### 3. Parser + Macro Layer (`plasTeX`)
- Parse LaTeX into a semantic AST with macro and environment expansion.
- Register built-in and project-specific macro/environment definitions.
- Normalize parser nodes into stable visitor events (`tag`, `env`, text, math, citation, etc.).
- Surface parser diagnostics for unknown macros, malformed input, and recovery paths.

### 4. Cross-Reference and Citation Subsystem
- Parse labels/targets and register anchors during traversal.
- Resolve references in a second pass or deferred resolution queue.
- Create internal hyperlinks in the output DOCX.
- Ingest bibliography artifacts (`.aux`, `.bcf`) for citation mapping.
- Provide a citation engine abstraction with a default numeric formatter and optional `citeproc` backend for CSL styles.

### 5. Math Bridge
- **Input**: inline and display LaTeX math.
- **Conversion**: LaTeX -> MathML (`latex2mathml`) -> OMML (`lxml` + `docx.oxml`).
- **Output**: inject OMML into the document tree.
- **Failure behavior**: if conversion fails, insert source math text and emit warning.

### 6. Styling and Theme Integration
- Use Word theme fonts (Major/Minor) by default.
- Central style mapping for headings, body text, code-like spans, and captions.
- Keep style behavior deterministic and template-friendly.

### 7. Figure and Float Handling
- Parse `figure` and `wrapfigure` environments as first-class content blocks.
- Resolve and place image assets from `\includegraphics` when available.
- Render captions from `\caption{...}` with a consistent Word caption style.
- Preserve figure labels for cross-reference integration (`\label` + `\ref`/`\autoref` paths).
- In permissive mode, degrade gracefully when image files are missing (retain caption/text + warning).

## Dependency Plan
- `plasTeX`: LaTeX parsing and macro/environment model.
- `python-docx`: DOCX/OOXML writing.
- `latex2mathml`: math conversion bridge.
- `lxml`: XML transforms/injection for OMML.
- `click`: CLI surface.

## Conversion Workflow
1. Load source into `plasTeX` and register project macro/environment definitions.
2. Initialize `LatexBridge` and register decorator handlers (`@latex.tag`, `@latex.env`).
3. Traverse AST through visitor dispatch and build document content.
4. Resolve deferred references/citations.
5. Resolve figure assets/captions and register figure anchors.
6. Emit diagnostics summary (warnings/errors).
7. Save DOCX.

## Error Handling and Fallbacks
- Unsupported command/environment: emit warning and preserve readable text when possible.
- Unknown macro in parser layer: warn and keep recoverable text output.
- Parse ambiguity: continue conversion, annotate diagnostics.
- Reference target missing: render placeholder text and warning.
- Math conversion failure: fallback to plain text math source.
- Provide strict mode (fail on first error) and permissive mode (default).

## Testing Strategy
1. **Unit tests**
   - `.aux` and `.bcf` parsing.
   - Label/reference resolver.
   - Escaping and special character normalization.
2. **Integration tests**
   - Golden fixtures: `.tex` input -> structural assertions on generated `.docx`.
   - Verify hyperlinks, heading levels, list nesting, and math blocks.
   - Verify citation formatting behaviors (single cite, multi-cite ordering, numeric range compression).
   - Verify figure/wrapfigure handling: image placement, caption text, and figure label links.
3. **Round-trip/real-world tests**
   - Compile representative LaTeX projects to generate realistic `.aux/.bcf` artifacts.
   - Parse those artifacts and verify citation/reference mapping.
4. **Regression suite**
   - Keep a corpus of previously failing snippets and lock behavior.

## Test Layout (proposed)
- `tests/unit/`
- `tests/integration/`
- `tests/regression/`
- `tests/fixtures/tex/` (input `.tex`)
- `tests/fixtures/aux/` and `tests/fixtures/bcf/` (citation/reference artifacts)
- `tests/fixtures/expected/` (small JSON snapshots for structural expectations)

## Initial 10 Test Cases
1. **section_heading_maps_to_word_heading**
   - Input: `\section{Intro}`.
   - Assert: first paragraph style is `Heading 1`, text is `Intro`.
2. **inline_formatting_bold_italic**
   - Input: `\textbf{B} \emph{I}`.
   - Assert: run-level bold and italic flags are preserved.
3. **itemize_nesting_depth_two**
   - Input: nested `itemize`.
   - Assert: list paragraphs exist with correct nesting/indent semantics.
4. **equation_block_math_injected_or_fallback**
   - Input: display math environment.
   - Assert: OMML node exists, or fallback text appears with warning in permissive mode.
5. **label_and_ref_internal_link**
   - Input: `\section{A}\label{sec:a} ... \ref{sec:a}`.
   - Assert: target anchor is created and `\ref` becomes internal hyperlink text.
6. **eqref_formats_parenthesized_reference**
   - Input: equation with `\label{eq:x}` and later `\eqref{eq:x}`.
   - Assert: rendered ref text includes parentheses and resolves to equation target.
7. **missing_reference_emits_warning_and_placeholder**
   - Input: `\ref{missing}` with no label.
   - Assert: warning is recorded; placeholder text is rendered.
8. **aux_parser_extracts_labels_and_citations**
   - Input: representative `.aux` fixture.
   - Assert: label map and citation keys parse deterministically.
9. **bcf_parser_extracts_bibliography_entries**
   - Input: representative `.bcf` fixture.
   - Assert: citation metadata fields required by renderer are extracted.
10. **unknown_macro_permissive_vs_strict_modes**
    - Input: document with unsupported macro.
    - Assert: permissive mode warns and continues; strict mode fails with explicit error.
11. **cite_compresses_numeric_ranges**
    - Input: `\cite{A,B,C,D,E}` with mapped numeric orders 1..5.
    - Assert: citation output compresses to `[1-5]` (style permitting).
12. **figure_caption_renders_consistently**
    - Input: `figure` + `\includegraphics` + `\caption`.
    - Assert: caption text is emitted in caption style and linked to figure label.
13. **wrapfigure_fallback_when_asset_missing**
    - Input: `wrapfigure` with missing image file and valid caption.
    - Assert: caption/text preserved with warning in diagnostics.

## Test Execution Policy
- Run unit + core integration tests on every PR.
- Run extended regression corpus in nightly CI.
- When fixing a bug, add a regression fixture before or with the fix.

## Milestones (priority order)
1. Finalize parser migration to `plasTeX` with visitor event normalization.
2. Implement labels/references and internal hyperlink generation.
3. Implement figure/wrapfigure pipeline with caption extraction and asset resolution.
4. Build parser and integration test harness.
5. Harden escaping and special character handling.
6. Implement citation engine with numeric range compression and citeproc integration path.
7. Add package-compatibility checks with Python equivalents/fallbacks.

## Open Questions
- Single-pass with deferred references vs explicit two-pass architecture?
- What is the minimum supported package set for v0.1?
- Should unsupported packages be hard warnings or configurable policy?
- Which parser internals should be exposed vs hidden behind stable decorator events?

## Known Gaps / TODO
- Citation style modes beyond numeric are not implemented yet:
  - Author-year output mode (for non-numeric bib styles) is pending.
- REVTeX note-like `\bibitem` entries that are cited numerically need dedicated classification:
  - Separate "reference entry" vs "note-like citation entry" behavior.
  - Prevent numeric range folding across mixed reference and note-like keys.
