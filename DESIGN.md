# Design Document: docxlate

## Overview
`docxlate` is a Python library that converts LaTeX documents into Microsoft Word (`.docx`) files using a declarative decorator model with extension modules. It uses `plasTeX` for LaTeX parsing/macro expansion and `python-docx` for document generation.

## Goals
- Convert common LaTeX structures into semantically correct Word content.
- Provide an extensible handler system for commands and environments.
- Preserve a clean visitor/decorator authoring interface for users.
- Support robust cross-references (`\label`, `\ref`, `\eqref`, citation links).
- Support citation formatting behaviors (numeric ranges like `[1-5]`, style-aware rendering).
- Handle floating content (`figure`, `wrapfigure`) with reliable caption rendering.
- Produce professional default output compatible with Word themes/templates.
- Fail gracefully when unsupported LaTeX features are encountered.

## Decision Snapshot (March 2026)
- `MacroSpec` is the required end-state registration contract for command/environment wiring.
- Compatibility fallback for decorators without `parse_class` is transitional and will be removed after migration completion.
- Feature policy and artifact handling (for example color and bibliography artifacts) should live in extensions, not in `LatexBridge`.
- Table MVP starts only after registry closure and extension ownership cleanup are complete.

## Architecture

### 1. Core Engine (`LatexBridge`)
Central conversion class.
- **Registry**: Maps LaTeX commands/environments to handlers.
- **Document state**: Owns a `python-docx` `Document` plus conversion context.
- **Visitor dispatch**: Recursively traverses the parsed AST and dispatches handlers.
- **Diagnostics**: Records warnings/errors with source context when possible.
- **Boundary**: Core should not host feature-specific artifact policy; those concerns belong to extensions.

### 2. Handler Layer
Handlers are user-defined (or default) functions registered with `@latex.command` and `@latex.env`.
- **Command handlers**: e.g., `\section`, `\textbf`, `\emph`, `\href`.
- **Environment handlers**: e.g., `equation`, `itemize`, `enumerate`, `figure`.
- **Lifecycle hooks/events**: pre-parse, pre-render, post-render.
- **Fallback handler**: called for unsupported commands/environments.

### 3. Plugin System (`ExtensionPlugin`)
To manage complexity and configuration for major features, `docxlate` uses a modular plugin system.
- **Definition**: Subclasses of `ExtensionPlugin` define a configuration model (Pydantic) and registration logic.
- **Registration**: Plugins are registered at startup and their configuration models are dynamically injected into the runtime validation schema.
- **Isolation**: Plugins like `bibliography`, `figure`, `hyperref`, `lists`, and `xcolor` encapsulate their own macros, handlers, and feature policy.

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
- Bibliography artifact loading should be extension-owned with a single-pass `.aux` pipeline per run.

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

### 9. Unified Macro Registration Contract
To prevent parser/renderer drift, macro registration must be unified under one contract.

- **Single source of truth**: define each macro/environment once as a `MacroSpec` containing:
  - `name`
  - `kind` (`command` or `env`)
  - `parse_class` (plasTeX macro/env class)
  - `handler` (runtime renderer callback)
  - `inline` (for command handlers)
  - `policy` (`render`, `stub`, `declaration`)
- **Single registration path**: plugins/core register only through `register_spec(...)`, never by separately calling parse and render registration APIs.
- **Automatic dual wiring**: `register_spec(...)` must wire both parser globals and runtime dispatch entries.
- **Decorator ergonomics retained**: decorator APIs can stay, but they must register through `MacroSpec` (with `parse_class`) rather than bypassing the registry.
- **Fail-fast validation at startup**:
  - `render` specs require both parse class and handler.
  - parse-only specs must be explicitly marked `stub` or `declaration`.
  - duplicate names or conflicting kinds are hard errors.
- **CI enforcement**:
  - registry integrity tests are mandatory.
  - legacy non-spec handler registrations are disallowed after migration cutoff.
  - unrecognized command/environment warnings fail tests unless explicitly allowlisted as parse-only policy entries.
- **Plugin compatibility**: each plugin returns a spec list and is validated through the same shared registry validator.

## Dependency Plan
- `plasTeX`: LaTeX parsing and macro/environment model.
- `python-docx`: DOCX/OOXML writing.
- `latex2mathml`: math conversion bridge.
- `lxml`: XML transforms/injection for OMML.
- `click`: CLI surface.
- `pydantic`: Configuration validation.

## Roadmap & Pending Work

### Table Support (Priority)
- Complete MacroSpec migration closure and extension ownership cleanup first.
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

### Macro Registration Hardening
- Introduce the shared `MacroSpec` model and registry module.
- Migrate built-in handlers/plugins (`hyperref`, `figure`, `bibliography`, `lists`) to spec-based registration.
- Migrate remaining core handlers/macros to spec-backed registration and remove transitional fallback paths.
- Add startup validation so parser and renderer registrations cannot diverge silently.
- Add regression tests for:
  - missing parse class for renderable macros,
  - parse-only macros without explicit parse-only policy,
  - duplicate/ambiguous macro registrations.
