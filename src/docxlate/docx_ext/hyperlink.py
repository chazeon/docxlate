from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

from docxlate.model import LinkTarget, TextSpan
from .run_style import new_run_properties_for_span


class HyperlinkWriter:
    def emit_span(self, paragraph, span: TextSpan, link: LinkTarget) -> bool:
        hyperlink = self._new_hyperlink_element(paragraph, link)
        if hyperlink is None:
            return False
        hyperlink.append(self._new_hyperlink_run_element(span))
        paragraph._p.append(hyperlink)
        return True

    def _new_hyperlink_element(self, paragraph, link: LinkTarget):
        hyperlink = OxmlElement("w:hyperlink")
        if link.anchor:
            hyperlink.set(qn("w:anchor"), link.anchor)
            return hyperlink
        if link.url:
            rel_id = link.rel_id
            if rel_id is None:
                rel_id = paragraph.part.relate_to(link.url, RT.HYPERLINK, is_external=True)
                link.rel_id = rel_id
            hyperlink.set(qn("r:id"), rel_id)
            return hyperlink
        return None

    def _new_hyperlink_run_element(self, span: TextSpan):
        run = OxmlElement("w:r")
        run.append(new_run_properties_for_span(span, default_char_role="Hyperlink"))
        text_node = OxmlElement("w:t")
        text_node.text = span.text
        run.append(text_node)
        return run
