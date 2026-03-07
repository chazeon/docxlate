# Execution TODO

Derived from [06_execution-plan.md](06_execution-plan.md).

## Decision Log

As of March 6, 2026, the following decisions are locked:

- [x] Enforce strict `MacroSpec` registration as the end-state (legacy decorator fallback is transitional only).
- [x] Complete extension ownership cleanup for color handling and bibliography artifacts before starting Table MVP.
- [x] Keep `core.py` focused on parser/traversal/render state engine concerns; move feature policy and artifact logic to extensions.

## Active

- [x] Guardrail Slice
  - [x] Introduce `MacroSpec` contract.
  - [x] Add startup validation:
    - [x] Renderable specs require parse class + handler.
    - [x] Parse-only specs must explicitly use `stub`.
    - [x] Duplicate/conflicting registrations fail fast.
  - [x] Apply `MacroSpec` path to new table extension first.
  - [x] Add registry integrity tests.

- [x] Broader Registry Migration (moved earlier per priority)
  - [x] Migrate `hyperref`, `figure`, `bibliography`, `lists` to `MacroSpec`.
  - [x] Preserve decorator ergonomics via spec-aware decorators.
  - [x] Add/refresh regression coverage for registration wiring.

## Next (Reprioritized)

- [ ] Priority 1: Finish MacroSpec migration closure (blocker for clean table rollout)
  - [ ] Complete **MacroSpec Completion Checklist (Handler Audit)** below.
  - [ ] Resolve high-impact ambiguity items needed for enforcement:
    - [ ] `MacroSpec` policy semantics (`render`/`stub`/`declaration`)
    - [ ] decorator strictness end-state (`parse_class` required or compatibility mode)
    - [ ] unknown-macro warning/allowlist CI policy

- [ ] Priority 2: Extract color handling into extension module
  - [ ] Complete **Refactor Plan: Extract Color Handling to `extensions/xcolor.py`** below.
  - [ ] Keep runtime behavior unchanged while moving ownership out of core handlers.

- [ ] Priority 3: Consolidate bibliography artifact ownership (`.aux`/`.bbl`/`.bcf`)
  - [ ] Complete **Audit Plan: Bibliography Artifact Ownership** below.
  - [ ] Remove duplicated `.aux` parsing passes and clarify module boundaries.

- [ ] Priority 4: Table MVP (after Priority 1 + 2 + 3)
  - [ ] Native `tabular` -> Word table rendering.
  - [ ] Template-aware table style resolution + deterministic fallback.
  - [ ] In-cell text/math/image rendering via existing pipelines.
  - [ ] `table` caption/label with `.aux` number resolution.

- [ ] Priority 5: Table Structural Expansion
  - [ ] `multicolumn` horizontal merging.
  - [ ] Sizing/alignment refinements.
  - [ ] XML-level regression tests.

- [ ] Priority 6: Core (`core.py`) cleanup and boundary tightening
  - [ ] Complete **Core Audit: `LatexBridge` abstraction and cleanup** below.

## MacroSpec Completion Checklist (Handler Audit)

Current gap: extension handlers are mostly spec-compliant, but core handlers in `src/docxlate/handlers.py` still use legacy registration paths.

- [ ] Convert core command handlers to explicit spec-backed decorators (`parse_class=...`):
  - [ ] `section`, `subsection`, `subsubsection`
  - [ ] `title`, `author`, `date`, `maketitle`
  - [ ] `noindent`, `indent`, `paragraph`
  - [ ] `Needspace`, `textcolor`, `and`
  - [ ] `$`, `math` (inline math commands)
- [ ] Convert core env handler `equation` to explicit spec-backed decorator (`parse_class=...`).
- [ ] Replace direct `latex.macro(...)` calls in `handlers.py` with explicit spec entries:
  - [ ] `and`, `color`, `textcolor`, `Needspace`
  - [ ] Use `policy="stub"` (or `declaration`) where parse-only behavior is intended.
- [ ] Remove remaining legacy parse wiring helpers once replaced (no duplicate parse registration paths).
- [ ] Add CI/registry integrity test that fails when any legacy registrations remain:
  - [ ] `command_handlers - macro_specs == empty`
  - [ ] `env_handlers - macro_specs == empty`
  - [ ] parse-only macros must appear in `macro_specs` with explicit non-render policy.
- [ ] Decide enforcement mode for decorators:
  - [ ] Keep temporary fallback (`@latex.command(...` without `parse_class`) during migration only.
  - [ ] Add strict mode (or direct failure) after migration completion.

Definition of done for migration:
- Every registered command/env/parse macro is represented by a `MacroSpec`.
- Startup validation catches missing parse class/handler and duplicate/conflicting registrations.
- Registry integrity test is mandatory in CI.

## Refactor Plan: Extract Color Handling to `extensions/xcolor.py`

### Evaluation Summary

- Current color support is split across `src/docxlate/handlers.py` and `src/docxlate/core.py`.
- `\textcolor{...}{...}` runtime rendering is in `handlers.py`.
- `\color{...}` declaration-style behavior is implemented in core walker (`_declaration_style_for_node`).
- Parse registration for color-related macros is currently legacy (`latex.macro(...)` in `handlers.py`).
- This is inconsistent with the plugin-style organization used by `hyperref`, `lists`, `figure`, and `bibliography`.

### Goal

Move color-related macro classes and handler registration into a dedicated extension module while preserving current behavior and MacroSpec guardrails.

### Required Changes

- [ ] Add `src/docxlate/extensions/xcolor.py` with:
  - [ ] `color` parse macro class (for declaration-style color scope).
  - [ ] `textcolor` parse macro class.
  - [ ] `register(latex)` that uses spec-aware registration.
- [ ] Register `\color` as explicit parse-only spec:
  - [ ] `policy="declaration"` (or `stub`, with clear rationale), no runtime handler.
- [ ] Register `\textcolor` as render spec:
  - [ ] Inline handler equivalent to existing `handle_textcolor`.
  - [ ] `parse_class` wired via spec-aware decorator.
- [ ] Update extension wiring:
  - [ ] Export `register_xcolor_extension` from `src/docxlate/extensions/__init__.py`.
  - [ ] Call `register_xcolor_extension(latex)` in `src/docxlate/handlers.py` startup sequence.
- [ ] Remove color-related legacy registrations from `handlers.py`:
  - [ ] Remove `Color` / `Textcolor` local class definitions.
  - [ ] Remove `latex.macro("color", ...)` and `latex.macro("textcolor", ...)`.
  - [ ] Remove in-file `handle_textcolor` function after move.

### Keep/Do Not Change

- [ ] Keep core declaration-style application in `_declaration_style_for_node` for now (lowest-risk behavior parity).
- [ ] Keep existing parse-compatibility logic for `xcolor` package skipping unchanged in this refactor.

### Test Plan

- [ ] Run:
  - [ ] `tests/integration/test_style_scope.py`
  - [ ] `tests/integration/test_core_rendering.py` (color + math interactions)
  - [ ] `tests/test_inline.py` (textcolor behavior)
- [ ] Add/adjust registry integrity checks so moved macros are represented in `macro_specs`.

### Risks

- [ ] Behavior drift in scoped color application (`\color` declaration semantics) if parse class args differ.
- [ ] Duplicate registration if legacy and extension paths coexist during transition.

### Done Criteria

- [ ] No color/textcolor registrations remain in core `handlers.py`.
- [ ] All color-related macros are registered through extension + MacroSpec path.
- [ ] Existing color/style tests pass unchanged.

## Audit Plan: Bibliography Artifact Ownership (`.aux` / `.bbl` / `.bcf`)

### Audit Findings

- `src/docxlate/extensions/bibliography/runtime.py` owns bibliography behavior but relies on root-level parsers:
  - `src/docxlate/bbl.py`
  - `src/docxlate/bcf.py`
  - `src/docxlate/aux.py` (`parse_abx_aux_cite_order`, and `parse_refs` for bibcite data)
- `.aux` is parsed in two separate load hooks:
  - bibliography load hook (for `bibcites` + cite order)
  - core handlers load hook (for `refs`)
- `bibcites` is populated but currently not consumed by runtime behavior (state appears unused).
- CLI command `check-bcf` imports parser functions directly from root `bcf.py`, so parser location is also a CLI/API concern.

### Target Ownership Model

- [ ] Bibliography extension should own bibliography artifact parsing pipeline end-to-end.
- [ ] Core should own only generic cross-reference label parsing needed outside bibliography.
- [ ] Root-level parser modules should either:
  - [ ] become thin compatibility wrappers, or
  - [ ] be clearly documented as shared artifact utilities.

### Required Refactor Work

- [ ] Split aux concerns:
  - [ ] keep `newlabel`/refs parsing in core/shared module
  - [ ] move biblatex cite-order parsing (`abx@aux@cite`) into bibliography extension artifact module
- [ ] Move/organize bibliography artifact parsers under extension (example target):
  - [ ] `extensions/bibliography/artifacts/bbl.py`
  - [ ] `extensions/bibliography/artifacts/bcf.py`
  - [ ] `extensions/bibliography/artifacts/aux.py`
- [ ] Replace double `.aux` file parse with one cached read per run (shared parse result in context).
- [ ] Decide fate of `bibcites`:
  - [ ] remove if unused
  - [ ] or document concrete runtime usage
- [ ] Preserve public import/API compatibility as needed:
  - [ ] keep `docxlate.bbl` / `docxlate.bcf` wrappers until deprecation window ends
  - [ ] keep CLI `check-bcf` behavior unchanged

### Tests & Validation

- [ ] Ensure existing parser unit tests remain green:
  - [ ] `tests/unit/test_bbl_parser.py`
  - [ ] `tests/unit/test_bcf_parser.py`
  - [ ] `tests/unit/test_aux_parser.py`
- [ ] Ensure bibliography/references integration remains green:
  - [ ] `tests/integration/test_citations.py`
  - [ ] `tests/integration/test_references.py`
- [ ] Add regression test for single-pass aux artifact load (no duplicate parse side-effects).

### Done Criteria

- [ ] Bibliography artifact code is extension-owned and no longer scattered across unrelated core modules.
- [ ] `.aux` parsing is not duplicated per run.
- [ ] CLI/API compatibility is maintained (or explicitly versioned/deprecated).

## Known Ambiguities (To Clarify)

- [ ] Document `MacroSpec` policy semantics with concrete examples:
  - [ ] when to use `render`
  - [ ] when to use `stub`
  - [ ] when to use `declaration`
- [ ] Define migration end-state for decorators:
  - [x] temporary compatibility for `@latex.command/@latex.env` without `parse_class` (transition only)
  - [x] strict enforcement plan and cutoff point (strict `MacroSpec` end-state approved)
- [ ] Document core handler parse-class mapping plan:
  - [ ] section/subsection/subsubsection
  - [ ] title/author/date/maketitle
  - [ ] paragraph/noindent/indent/Needspace
  - [ ] equation and inline math commands
- [ ] Document extension registration order dependencies and rationale.
- [ ] Document unknown-macro warning policy and CI enforcement:
  - [ ] strict vs allowlisted behavior
  - [ ] where allowlist lives
- [ ] Track baseline known test failures explicitly (pre-existing vs regression).
- [ ] Document color behavior split contract:
  - [x] declaration-style color application in core (temporary during extraction)
  - [x] command-level color handlers in extension (target ownership)
- [ ] Mark current table status explicitly:
  - [ ] MacroSpec stubs are present
  - [ ] native DOCX table rendering not yet implemented
- [ ] Document global singleton/runtime state expectations:
  - [ ] shared `latex` bridge instance
  - [ ] required reset behavior in tests and CLI runs
- [ ] Document deprecation/removal path for direct `latex.macro(...)` legacy registrations.

## Core Audit: `LatexBridge` abstraction and cleanup

### Audit Findings (Current State)

- `src/docxlate/core.py` is ~1030 lines and mixes multiple responsibilities:
  - parser setup + parse fallback policy
  - registry validation and registration APIs
  - AST traversal/dispatch
  - inline/declaration style semantics
  - paragraph/layout state machine
  - plugin-specific helper surfaces (figure/wrap emit passthrough)
- Core contains feature-specific logic that should live in feature modules:
  - `DocxlateDirectiveTokenizer` hardcodes `figure.wrap.*` directives
  - `_parse_source` hardcodes `xcolor` package-skip retry behavior
  - figure/wrap emitter passthrough methods expose figure-specific backend concepts
- Registration remains in mixed mode:
  - spec-based registration exists
  - legacy decorator fallback still allowed when `parse_class` omitted
  - full enforcement of “all handlers represented by MacroSpec” is not complete
- `context` usage is heavily string-keyed (`_preserve_paragraph_once`, `_trim_next_leading_space_once`, etc.) and acts as an implicit global state channel.
- `run(self, tex_source, aux_path=None)` has an unused parameter (`aux_path`), which suggests API drift.
- `self.aux_data` is present in bridge state but appears unused in current flow.

### Required Refactor Work

- [ ] Split bridge into clearer subsystems (incremental, not big-bang):
  - [ ] parser pipeline (`parse_source`, sanitize/retry/fallback)
  - [ ] traversal/dispatch engine (`_walk`, node helpers)
  - [ ] paragraph/render state management (frame + whitespace + paragraph flush rules)
  - [ ] registration/registry API surface
- [ ] Move feature-specific policy out of core:
  - [ ] move figure directive tokenization pattern out of core tokenizer (or make extensible hook registry)
  - [ ] move xcolor parse-skip heuristics to extension/config compatibility layer
  - [ ] reduce figure-specific wrapper methods on `LatexBridge` to a smaller backend capability boundary
- [ ] Complete registration enforcement:
  - [ ] remove/lock down legacy fallback registration path
  - [ ] ensure all active handlers/macros are represented via `MacroSpec`
- [ ] Improve state safety:
  - [ ] replace ad-hoc context string flags with typed state object or named state container
  - [ ] document context key ownership by subsystem
- [ ] Remove API drift/dead fields:
  - [ ] deprecate/remove unused `aux_path` from `run(...)` or wire it intentionally
  - [ ] remove or document purpose of `aux_data`

### Validation / Regression

- [ ] Add bridge-level tests around paragraph flush state transitions (par/env/command interactions).
- [ ] Add strict registry integrity test that fails on legacy non-spec handler registrations.
- [ ] Keep integration suites green during extraction:
  - [ ] core rendering
  - [ ] style scope
  - [ ] references/citations
  - [ ] figures/lists

### Done Criteria

- [ ] `core.py` no longer contains feature-specific hardcoded behaviors that belong to extensions.
- [ ] Registry path is singular (MacroSpec-backed) for active handlers.
- [ ] Bridge state transitions are explicit/tested instead of implicit string-key coordination.
