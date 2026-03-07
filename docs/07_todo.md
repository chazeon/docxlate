# Execution TODO

Derived from [06_execution-plan.md](06_execution-plan.md).

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

## Next

- [ ] Table MVP
  - [ ] Native `tabular` -> Word table rendering.
  - [ ] Template-aware table style resolution + deterministic fallback.
  - [ ] In-cell text/math/image rendering via existing pipelines.
  - [ ] `table` caption/label with `.aux` number resolution.

- [ ] Table Structural Expansion
  - [ ] `multicolumn` horizontal merging.
  - [ ] Sizing/alignment refinements.
  - [ ] XML-level regression tests.

- [ ] Broader Registry Migration
  - [x] Migrate `hyperref`, `figure`, `bibliography`, `lists` to `MacroSpec`.
  - [ ] Keep CI checks for registry integrity and unknown-macro warning policy.
