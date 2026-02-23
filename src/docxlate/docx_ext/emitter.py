from __future__ import annotations
from contextlib import contextmanager

from docxlate.model import EquationSpec, LinkTarget, TextSpan
from docxlate.utils import apply_theme_font, inject_omml
from .hyperlink import HyperlinkWriter
from .run_style import apply_text_span_style


class DocxEmitterBackend:
    """
    DOCX emission backend for resolved inline spans and equation specs.
    Keeps OOXML-specific logic out of core traversal/dispatch.
    """

    def __init__(self, context: dict):
        self.context = context
        self._active_link: LinkTarget | None = None
        self._hyperlinks = HyperlinkWriter()

    def begin_paragraph(
        self,
        doc,
        *,
        role: str | None = None,
        style_name: str | None = None,
        style_table: dict | None = None,
    ):
        resolved = style_name or self._resolve_paragraph_style(doc, role, style_table)
        if resolved:
            return doc.add_paragraph(style=resolved)
        return doc.add_paragraph()

    def begin_link(self, target: LinkTarget):
        if self._active_link is not None:
            raise RuntimeError("Nested hyperlinks are not supported")
        self._active_link = target

    def end_link(self):
        self._active_link = None

    @contextmanager
    def link_scope(self, target: LinkTarget):
        self.begin_link(target)
        try:
            yield
        finally:
            self.end_link()

    def has_active_link(self) -> bool:
        return self._active_link is not None

    def emit_span(self, paragraph, span: TextSpan):
        if self._active_link is None:
            self._emit_plain_span(paragraph, span)
            return
        self._emit_linked_span(paragraph, span, self._active_link)

    def emit_equation(self, paragraph, spec: EquationSpec):
        xsl_path = self.context.get("mathml2omml_xsl_path")
        ok = inject_omml(
            paragraph,
            spec.latex,
            xsl_path=xsl_path,
            color=spec.color,
            display=spec.display,
        )
        if not ok and not xsl_path:
            self._warn_missing_math_xsl()
        if spec.number:
            run = paragraph.add_run(f" ({spec.number})")
            apply_theme_font(run, "minor")

    def _emit_plain_span(self, paragraph, span: TextSpan):
        run = paragraph.add_run(span.text)
        if span.char_role:
            try:
                run.style = span.char_role
            except Exception:
                pass
        apply_text_span_style(run, span)

    def _emit_linked_span(self, paragraph, span: TextSpan, link: LinkTarget):
        if not self._hyperlinks.emit_span(paragraph, span, link):
            self._emit_plain_span(paragraph, span)

    def _warn_missing_math_xsl(self):
        msg = (
            "Math OMML stylesheet path is not configured "
            "(set mathml2omml_xsl_path in config)."
        )
        warnings = self.context.setdefault("warnings", [])
        if msg not in warnings:
            warnings.append(msg)

    def _resolve_paragraph_style(self, doc, role: str | None, style_table: dict | None):
        if not role or not style_table:
            return None
        candidates = style_table.get(role, [])
        if isinstance(candidates, str):
            candidates = [candidates]
        paragraph_styles = [style for style in doc.styles if style.type == 1]
        styles_by_name = {style.name: style for style in paragraph_styles}
        style_name_by_id = {style.style_id: style.name for style in paragraph_styles}
        for candidate in candidates:
            if candidate in styles_by_name:
                return candidate
            resolved_name = style_name_by_id.get(candidate)
            if resolved_name:
                return resolved_name
        return None
