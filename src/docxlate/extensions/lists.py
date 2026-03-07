from __future__ import annotations

from plasTeX.Base.LaTeX.Lists import (
    List as PlastexList,
    enumerate_ as plastex_enumerate,
    itemize as plastex_itemize,
)

from docxlate.docx_ext import DocxOxmlNumberingBackend

def register(latex):
    backend = latex.context.get("numbering_backend")
    if backend is None:
        backend = DocxOxmlNumberingBackend()
        latex.context["numbering_backend"] = backend

    @latex.env("itemize", parse_class=plastex_itemize)
    def handle_itemize(node):
        stack = latex.context.setdefault("list_stack", [])
        stack.append({"type": "itemize", "counter": 0})
        latex.render_nodes(node.childNodes)
        stack.pop()
        backend.cleanup_list_gaps(latex.doc)

    @latex.env("enumerate", parse_class=plastex_enumerate)
    def handle_enumerate(node):
        stack = latex.context.setdefault("list_stack", [])
        stack.append({"type": "enumerate", "counter": 0})
        latex.render_nodes(node.childNodes)
        stack.pop()
        backend.cleanup_list_gaps(latex.doc)

    @latex.command("item", parse_class=PlastexList.item)
    def handle_item(node):
        stack = latex.context.get("list_stack", [])
        current = stack[-1] if stack else {"type": "itemize", "counter": 0}
        list_type = current.get("type", "itemize")
        level = len(stack) if stack else 1
        p = latex.doc.add_paragraph()
        backend.apply_list_numbering(p, list_type, level)
        latex._current_paragraph = p
        latex.context["_preserve_paragraph_once"] = True

    return None
