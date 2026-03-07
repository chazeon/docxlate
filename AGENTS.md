# Agent Notes

## Word Recovery Guardrails (DOCX/OMML)

- Do not treat XML well-formedness as sufficient; Word open/recovery behavior is the real compatibility check.
- For math color in OMML, prefer Word-safe run properties:
  - use `w:rPr` directly under `m:r`
  - avoid `m:rPr/m:ctrlPr` injection under math runs
- Validate with real conversion conditions when debugging:
  - real `docxlate.yaml`
  - real `.aux` / `.bbl`
  - real image assets
- When a recovery bug appears, bisect generated DOCX slices first to isolate the exact fragment.
- Every recovered production bug must add a direct regression test for the exact triggering pattern.
