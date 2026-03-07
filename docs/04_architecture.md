# Architecture

`docxlate` is designed with a clear separation between LaTeX parsing and Word document generation.

## High-Level Overview

1.  **Parsing**: LaTeX source is parsed using `plasTeX` into an Abstract Syntax Tree (AST).
2.  **Bridging**: The `LatexBridge` traverses the AST.
3.  **Handling**: Registered handlers (decorators like `@latex.command` and `@latex.env`) process specific LaTeX nodes through `MacroSpec` registration.
4.  **Emitting**: Handlers call backend-agnostic methods (e.g., `emit_text`, `begin_paragraph`) that are then implemented by the DOCX backend.
5.  **Artifact Integration**: Extensions and shared parsers load `.aux`, `.bbl`, and `.bcf` artifacts to resolve cross-references and citations with high fidelity.

## Core Components

### LatexBridge

The `LatexBridge` is the central engine of `docxlate`. It:
- Maintains the document state and conversion context.
- Dispatches handlers based on the LaTeX command or environment.
- Manages the style stack for inline formatting.
- Collects diagnostics and warnings.
- Enforces registry integrity checks before render execution.

`LatexBridge` is intended to be a traversal/render engine, not a feature-policy host. Feature-specific logic should live in extensions.

### Handler Layer

Handlers define how LaTeX structures are mapped to Word.

- **Command Handlers**: Registered with `@latex.command`, these handle inline commands like `\\textbf` or block commands like `\\section`.
- **Environment Handlers**: Registered with `@latex.env`, these handle environments like `itemize`, `figure`, or `equation`.

### Artifact Parsers

- **Core reference parsing**: Extracts label/reference metadata used by generic cross-reference flows.
- **Bibliography artifact parsing**: Bibliography extension owns citation-order and entry parsing (`.aux`/`.bbl`/`.bcf`) for citation/bibliography rendering.
- **Loading policy**: Prefer single-pass artifact loading per run to avoid duplicate `.aux` parse flows.

### DOCX Backend (`docx_ext`)

Since `python-docx` does not support all Word features natively (especially advanced OOXML structures), `docxlate` includes an extension layer for:
- Floating images and text boxes.
- Internal hyperlinks and bookmarks.
- Math (OMML) injection.
- Complex numbering schemes.

## Plugin System

`docxlate` uses a modular plugin architecture to manage configuration and runtime behavior for major features like bibliography and figures.

### ExtensionPlugin

Plugins are defined by subclassing `ExtensionPlugin`. A plugin is responsible for:
1.  **Config Model**: Defining a Pydantic `BaseModel` for its configuration.
2.  **Runtime Registration**: Registering its own LaTeX macros and handlers on the `LatexBridge`.
3.  **Config Application**: Mapping validated configuration values into the global conversion context.

## Composition & Style Resolution

To avoid nesting-order bugs (e.g., `\\textbf{\\href{...}{...}}` vs `\\href{...}{\\textbf{...}}`), rendering is split into explicit layers:

- **Intent events**: walker/handlers emit semantic intent (`link-start`, `link-end`, `text`, `math`, `citation`, heading/list roles).
- **Style state stack**: maintain merged inline state (bold/italic/small-caps/monospace/color/etc.) with push/pop deltas per node scope.
- **Compositor**: convert intent + resolved style state into ordered inline spans/runs.
- **DOCX backend**: emit spans using `python-docx` first; use isolated OOXML extension points only where API support is missing.

### Boundary-Safe Render Context Contract

Core traversal uses typed context objects rather than plain dict threading:
- `RenderContext`
  - `style: StyleState` (resolved inline state at current point)
  - `char_role: Optional[str]` (character style role)
  - `para_role: Optional[str]` (paragraph semantic role; used when paragraph emission hooks need it)
- `SpanCompositor`
  - Input: `text + base RenderContext + optional style delta + optional char role override`
  - Output: `TextSpan(style, char_role)` for backend emission.

**Boundary rules:**
- Entering a group/child walk pushes a derived `RenderContext`; leaving pops automatically by recursion return.
- Declaration commands (e.g., `\\bfseries`) mutate the current sibling-stream context (left-to-right) and therefore affect following siblings in the same scope.
- Inline commands (e.g., `\\textbf{...}`) derive a child-only context and do not mutate sibling-stream context.
- `render_frame(style=...)` accepts mapping or typed context; mappings are composited against the active frame context.
- Backends do not infer style inheritance; they only emit already-resolved `TextSpan`.
- Block emit entry points (notably equation and caption) must source paragraph role from `RenderContext.para_role` when no explicit paragraph is passed.

**Planned backend API surface:**
- `begin_paragraph(role)` / `end_paragraph()`
- `emit_text(text, style_state)`
- `begin_link(target)` / `end_link()`
- `emit_math(source, mode)`
- `emit_image(spec)` / `begin_caption(role)` / `end_caption()`
- `begin_list(kind, level)` / `emit_list_item()` / `end_list()`

**Current status:**
- Figure/image insertion and wrapped-caption anchoring are emitted through backend methods; extension handlers orchestrate intent and sizing only.

### Caption Content Model
- Captions are structured containers, not plain-text-only fields.
- Caption rendering must reuse normal inline pipeline so content like math, links, citations, and inline styles is preserved.

### Style Resolution Rules
- **Semantic roles** provide defaults (e.g., hyperlink role, heading role).
- **Inline macros** apply partial deltas (set/unset only touched properties).
- **Final run properties** are computed at emit time from merged state.
- **Run segmentation** occurs only when effective style changes.

### Declaration Semantics (Walk-time)
- Resolve declarations strictly left-to-right during traversal.
- Declaration-style commands (e.g., `\\color{...}`, `\\bfseries`) affect only following siblings within current scope.
- Group boundaries (`{ ... }`) push/pop style state; declarations do not retroactively affect prior text.
- Backend emission must not infer or back-propagate style to already-emitted content.

### Color Handling Policy
- Track color as part of inline `StyleState` and resolve it during walk-time scope composition.
- Apply resolved color directly to text runs (`w:rPr/w:color`) in backend emission.
- For math, color must be propagated through math emission (OMML math run properties), not only text run properties.
- **Compatibility guard**: avoid direct OMML run-property rewrites that trigger Word document recovery; keep math-color as a deferred compatibility task until validated with Word.

## Numbering & Reference Policy

A core goal of `docxlate` is to ensure that numbering in Word matches the LaTeX project state exactly. To achieve this, we follow a strict "Source of Truth" policy:

### 1. Artifact-Driven Numbering
For all referenced elements (equations, figures, tables), the displayed number **must** come from LaTeX run artifacts (`.aux` label mapping), not from local DOCX-side counters.
- **Equations**: Displayed equation numbers are injected during the `equation` env rendering pass. The emitter uses OMML equation-array alignment (`m:oMathPara`/`m:eqArr`) to place the number on the right.
- **Figures/Tables**: Caption numbers are derived from the artifact label map.

### 2. Reference Consistency
- Any reference command (like `\\ref`, `\\eqref`, or `\\autoref`) **must** reuse the same resolved number source as the caption/equation it points to.
- `\\eqref` rendering is specifically contracted to include parentheses (e.g., `(1.1)`) regardless of whether they are present in the artifact label.

### 3. Missing Metadata Fallback
- If a label exists but is missing from the `.aux` data, the system renders a `[?]` placeholder and emits a diagnostic warning.
- Deriving "estimated" numbers for unlabeled equations or figures without TeX artifacts is explicitly out-of-scope to prevent numbering drift.

## Macro Classification System

To prevent drift between the parser (plasTeX) and the renderer (LatexBridge), macros are classified into explicit kinds:

- **Declarations**: Commands that mutate the current sibling-stream context (e.g., `\\bfseries`, `\\itshape`, `\\color`). They affect all following siblings in the same scope.
- **Inlines/Blocks/Envs**: Standard content containers that derive a child-only context (e.g., `\\section`, `\\textbf`, `itemize`).
- **Stubs**: Parse-only no-op wrappers. These are registered in the parser to prevent "Unknown Macro" errors but are explicitly marked to emit no output in the backend (e.g., internal BibLaTeX scaffolding macros).

### Registry Validation
The system is designed to detect:
- Macros declared as renderable without a corresponding parse signature.
- Accidental parse-only registration for commands expected to emit output.
- Duplicate/conflicting registrations for the same macro name.

### Registration Enforcement
- `MacroSpec` is the required registration contract end-state.
- Decorator fallback without `parse_class` is disabled by default.
  - Compatibility mode is explicit opt-in only (`LatexBridge(strict_macro_specs=False)`).

### `MacroSpec` Policy Semantics
- `policy="render"`: parse + render required.
  - Must provide both `parse_class` and `handler`.
  - Example: `\section`, `\cite`, `itemize`.
- `policy="stub"`: parse-only compatibility no-op.
  - Must provide `parse_class`; must not provide `handler`.
  - Example: parse scaffolding macros that should not emit output.
- `policy="declaration"`: parse-only declaration that mutates style/context in the walker.
  - Must provide `parse_class`; must not provide `handler`.
  - Example: `\color` updates active style scope in `_declaration_style_for_node`.

## OOXML Usage Policy
- Prefer `python-docx` for paragraph/run/style operations.
- Keep direct OOXML manipulation in `docx_ext` modules only (hyperlinks, bookmarks, advanced numbering, OMML injection, floating anchors).
- Core walker/handlers must not construct raw OOXML directly.
