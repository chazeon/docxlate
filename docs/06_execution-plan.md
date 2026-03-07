# Execution Plan: Macro Registration vs Table Work

## Decision

Do a **small unified macro registration guardrail first**, then implement table features.

## Why This Order

- Table support introduces several new parse/render touchpoints (`table`, `tabular`, `multicolumn`, caption/label flow).
- The current split registration approach (parse-time macro classes vs render-time handlers) is easy to mis-wire.
- A minimal registry validator first reduces rework and prevents silent integration drift during table rollout.

## Step-by-Step Plan

1. **Guardrail Slice (first)**
   - Introduce a lightweight `MacroSpec` contract.
   - Add startup validation:
     - renderable macros must have both parse class and handler;
     - parse-only entries must be explicitly marked `stub`;
     - duplicate/conflicting registrations fail fast.
   - Apply this contract to the new table plugin path first.

2. **Table MVP (second)**
   - Implement `tabular` rendering to native Word tables.
   - Apply template-aware table style resolution with deterministic fallback.
   - Render text/math/image inside cells through existing inline/math/image pipeline.
   - Implement `table` caption/label handling with `.aux`-driven number resolution.

3. **Table Structural Expansion**
   - Add `multicolumn` support (horizontal merging).
   - Add sizing/alignment refinements and additional XML-level regression tests.

4. **Broader Registry Migration**
   - Incrementally migrate existing plugins (`hyperref`, `figure`, `bibliography`, `lists`) onto `MacroSpec`.
   - Keep CI checks for registry integrity and unknown macro warnings policy.

## Deliverable Criteria

- New table feature work cannot ship with parse/render registration drift.
- Table MVP is functional with template style fidelity and in-cell math/image support.
- Integrity tests enforce the registration contract.
