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

### 3. Plugin System (`ExtensionPlugin`)
To manage complexity and configuration for major features, `docxlate` uses a modular plugin system.
- **Definition**: Subclasses of `ExtensionPlugin` define a configuration model (Pydantic) and registration logic.
- **Registration**: Plugins are registered at startup and their configuration models are dynamically injected into the runtime validation schema.
- **Isolation**: Plugins like `bibliography` and `figure` encapsulate their own macros, handlers, and artifact parsing logic.

### 4. Parser + Macro Layer (`plasTeX`)
- Parse LaTeX into a semantic AST with macro and environment expansion.
- Register built-in and project-specific macro/environment definitions.
- Normalize parser nodes into stable visitor events (`tag`, `env`, text, math, citation, etc.).
- **Directive Tokenization**: A custom tokenizer identifies `% docxlate: ...` comments during the earliest stage of parsing and injects them as internal commands.

### 5. Cross-Reference and Citation Subsystem
- Parse labels/targets and register anchors during traversal.
- Resolve references in a second pass or deferred resolution queue.
- Create internal hyperlinks in the output DOCX.
- Ingest bibliography artifacts (`.aux`, `.bcf`) for citation mapping.
- Provide a citation engine abstraction with a default numeric formatter and optional `citeproc` backend for CSL styles.

### 6. Math Bridge
- **Input**: inline and display LaTeX math.
- **Conversion**: LaTeX -> MathML (`latex2mathml`) -> OMML (`lxml` + `docx.oxml`).
- **Output**: inject OMML into the document tree.
- **Failure behavior**: if conversion fails, insert source math text and emit warning.

### 7. Styling and Theme Integration
- Use Word theme fonts (Major/Minor) by default.
- Central style mapping for headings, body text, code-like spans, and captions.
- Keep style behavior deterministic and template-friendly.

### 8. Inline Composition and Backend Boundary
To avoid nesting-order bugs, rendering is split into explicit layers:
- **Intent events**: walker/handlers emit semantic intent.
- **Style state stack**: maintain merged inline state (bold/italic/monospace/color/etc.).
- **Compositor**: convert intent + resolved style state into ordered inline spans/runs.
- **DOCX backend**: emit spans using `python-docx` first; use isolated OOXML extension points (`docx_ext`) only where API support is missing.

## Dependency Plan
- `plasTeX`: LaTeX parsing and macro/environment model.
- `python-docx`: DOCX/OOXML writing.
- `latex2mathml`: math conversion bridge.
- `lxml`: XML transforms/injection for OMML.
- `click`: CLI surface.
- `pydantic`: Configuration validation.

## Roadmap & Pending Work

### Table Support (Priority)
- Map table/cell rendering to DOCX template styles (e.g., `Table Grid`).
- Support header row emphasis, border models, cell padding, and alignment.
- Handle multi-row/multi-column merging.

### Citation & Bibliography
- Author-year output mode (for non-numeric bib styles).
- REVTeX note-like `\bibitem` entries classification.
- Full `citeproc` integration for CSL styles.

### Layout & Figures
- `wrapfigure` placement: Add `i`/`o` (inside/outside) anchoring for mirrored page layouts.
- Support for subfigures and more complex float layouts.

### Testing & Tooling
- **Markdown/TXT writer**: A lightweight writer that emits structural output without DOCX-specific formatting noise for deterministic testing.
- Enhanced diagnostic reporting with source line/column info for all warnings.
