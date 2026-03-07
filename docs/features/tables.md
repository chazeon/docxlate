# Tables (Feature Plan)

This document defines the implementation plan for table support in `docxlate`.

## Goals

- Render LaTeX `tabular`/`table` into native Word tables (`w:tbl`).
- Prioritize template table styles and preserve themed appearance.
- Support mixed cell content (text, inline/display math, images).
- Keep reference/caption numbering artifact-driven (`.aux` as source of truth).

## Target Outcomes

From `ada.docx`, we need to reliably support:

- Themed table styles (`TableGrid`, custom `Style2`, `GridTable4`).
- Equations inside cells (`m:oMath`, `m:oMathPara`).
- Images inside cells (`w:drawing` / `a:blip`).
- Cell-level alignment (for example centered content in selected cells).

## Existing API/Architecture We Will Reuse

- Core dispatch and render-frame stack in `LatexBridge`.
- Existing inline render pipeline for text style composition.
- Existing math and image emission in `DocxEmitterBackend`.
- Existing reference resolver for `\label` and `\ref` anchors.
- Existing plugin structure (`ExtensionPlugin`) used by figure/bibliography.

## Implementation Plan

### Phase 1: Core Table Rendering (MVP)

1. Add a `table` extension plugin and register it from `handlers.py` and `extensions/__init__.py`.
2. Add macro/environment definitions for `table`, `tabular`, `multicolumn` (parse-safe registration).
3. Implement `tabular` environment handler:
   - Build `doc.add_table(rows, cols)`.
   - Resolve style from config/template candidates, defaulting to `Table Grid`.
   - Render cell content with `render_frame(paragraph=cell.paragraphs[0])` so existing text/math/image handlers work in-cell.
   - Apply per-cell paragraph alignment from parsed cell style (`text-align`).
4. Implement `table` environment handler:
   - Render contained `tabular`.
   - Capture `caption` and `label`.
   - Resolve table number from `refs` (`.aux`) and register internal anchor.

### Phase 2: Structural Fidelity

1. Add `\multicolumn` support using horizontal merge (`gridSpan` behavior via cell merge API).
2. Add row/column sizing controls (where data is available from source).
3. Add table/row style toggles relevant to themed output (first row, banding behavior where applicable).

### Phase 3: Extended Compatibility

1. Add `\multirow` support (careful handling due to package parse complexity).
2. Improve fallback behavior for malformed/unsupported table constructs while keeping content visible.
3. Add advanced config knobs for style preference and layout defaults.

## Configuration Plan

Introduce `plugins.table` with conservative initial settings:

- `style_candidates`: ordered list of table style names/IDs.
- `fallback_style`: default style if candidates are unavailable.
- `autofit`: bool.
- `header`: options for first-row emphasis behavior.

## Testing Plan

Add integration tests that verify produced DOCX XML:

1. `tabular` creates `w:tbl` with expected row/column structure.
2. Chosen table style appears as `w:tblStyle`.
3. Inline and display math appear inside table cells.
4. Images appear inside table cells.
5. Cell alignment emits expected paragraph alignment XML.
6. `multicolumn` creates merged cells (phase 2).
7. `table` caption/label uses `.aux` number mapping and `\ref` consistency.

## Risks and Mitigations

- `plasTeX` table edge cases can produce unstable row tokenization when row breaks are ambiguous.
  - Mitigation: define supported row-break conventions for MVP and keep graceful fallback.
- `multirow` package parsing can trigger parser fallback warnings.
  - Mitigation: defer to phase 3 and isolate parse-time compatibility logic.
- Template style naming can vary (`style name` vs `styleId`).
  - Mitigation: resolve both names and IDs, matching current paragraph style resolution strategy.

## Definition of Done (Phase 1)

- Table environments render as native Word tables.
- Template style is applied when present; deterministic fallback works.
- Math and image content remain intact inside cells.
- Basic table caption/label/reference flow works with `.aux` numbers.
- Integration tests pass for the above behavior.
