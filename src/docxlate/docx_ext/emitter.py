from __future__ import annotations

from docxlate.model import EquationSpec, LinkTarget, TextSpan
from docxlate.utils import apply_theme_font, inject_omml
from .hyperlink import _emit_linked_span


class DocxEmitterBackend:
    """
    DOCX emission backend for resolved inline spans and equation specs.
    Keeps OOXML-specific logic out of core traversal/dispatch.
    """

    def __init__(self, context: dict):
        self.context = context
        self._active_link: LinkTarget | None = None

    def begin_paragraph(self, doc, *, role: str | None = None, style_name: str | None = None):
        # `role` is accepted for backend contract completeness; style resolution is
        # currently performed by the caller and passed as `style_name`.
        _ = role
        if style_name:
            return doc.add_paragraph(style=style_name)
        return doc.add_paragraph()

    def begin_link(self, target: LinkTarget):
        if self._active_link is not None:
            raise RuntimeError("Nested hyperlinks are not supported")
        self._active_link = target

    def end_link(self):
        self._active_link = None

    def emit_span(self, paragraph, span: TextSpan):
        if self._active_link is None:
            self._emit_plain_span(paragraph, span)
            return
        self._emit_linked_span(paragraph, span, self._active_link)

    def emit_equation(self, paragraph, spec: EquationSpec):
        xsl_path = self.context.get("mathml2omml_xsl_path")
        ok = inject_omml(paragraph, spec.latex, xsl_path=xsl_path)
        if not ok and not xsl_path:
            self._warn_missing_math_xsl()
        if spec.number:
            run = paragraph.add_run(f" ({spec.number})")
            apply_theme_font(run, "minor")

    def _apply_run_style(self, run, span: TextSpan):
        apply_theme_font(run, span.style.theme or "minor")
        if span.style.monospace:
            run.font.name = "Courier New"
        if span.style.bold:
            run.bold = True
        if span.style.italic:
            run.italic = True
        if span.style.small_caps:
            run.font.small_caps = True

    def _emit_plain_span(self, paragraph, span: TextSpan):
        run = paragraph.add_run(span.text)
        if span.char_role:
            try:
                run.style = span.char_role
            except Exception:
                pass
        self._apply_run_style(run, span)

    def _emit_linked_span(self, paragraph, span: TextSpan, link: LinkTarget):
        if not _emit_linked_span(paragraph, span, link):
            self._emit_plain_span(paragraph, span)

    def _warn_missing_math_xsl(self):
        msg = (
            "Math OMML stylesheet path is not configured "
            "(set mathml2omml_xsl_path in config)."
        )
        warnings = self.context.setdefault("warnings", [])
        if msg not in warnings:
            warnings.append(msg)
