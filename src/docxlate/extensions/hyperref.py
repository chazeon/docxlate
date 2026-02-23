from __future__ import annotations

import re

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from plasTeX import Command


class href(Command):
    args = "url:str self"


class hyperref(Command):
    args = "[ label:idref ] self"


class eqref(Command):
    args = "label:idref"


class ref(Command):
    args = "label:idref"


class label(Command):
    args = "label:id"


class ReferenceResolver:
    def __init__(self, context: dict):
        self.context = context
        self._ensure_state()

    def _ensure_state(self):
        self.context.setdefault("labels", {})
        self.context.setdefault("warnings", [])
        self.context.setdefault("_bookmark_id", 1)

    def _anchor_name(self, label_name: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", label_name).strip("_")
        return f"ref_{clean or 'target'}"

    def anchor_name(self, label_name: str) -> str:
        return self._anchor_name(label_name)

    def _ref_text_from_aux(self, label_name: str) -> str | None:
        refs = self.context.get("refs", {})
        info = refs.get(label_name)
        if not info:
            return None
        ref_num = info.get("ref_num")
        if ref_num is None:
            return None
        return str(ref_num)

    def _ensure_paragraph(self, latex):
        if latex._current_paragraph is not None:
            return latex._current_paragraph
        if latex.doc.paragraphs:
            return latex.doc.paragraphs[-1]
        latex._ensure_paragraph()
        return latex._current_paragraph

    def register_label(self, latex, label_name: str, ref_text: str | None = None):
        self._ensure_state()
        paragraph = self._ensure_paragraph(latex)
        if paragraph is None:
            return

        anchor_name = self._anchor_name(label_name)
        bookmark_id = str(self.context["_bookmark_id"])
        self.context["_bookmark_id"] += 1

        start = OxmlElement("w:bookmarkStart")
        start.set(qn("w:id"), bookmark_id)
        start.set(qn("w:name"), anchor_name)
        end = OxmlElement("w:bookmarkEnd")
        end.set(qn("w:id"), bookmark_id)
        paragraph._p.append(start)
        paragraph._p.append(end)

        resolved_ref_text = ref_text or self._ref_text_from_aux(label_name) or "?"
        self.context["labels"][label_name] = {
            "anchor": anchor_name,
            "ref_text": str(resolved_ref_text),
        }

    def resolve_ref_text(self, label_name: str) -> str:
        self._ensure_state()
        from_aux = self._ref_text_from_aux(label_name)
        if from_aux is not None:
            return from_aux
        labels = self.context.get("labels", {})
        info = labels.get(label_name)
        if info is None:
            self.context.setdefault("warnings", []).append(
                f"Missing reference target: {label_name}"
            )
            return "?"
        return info.get("ref_text", "?")

    def append_internal_link(self, latex, label_name: str, text: str):
        self._ensure_state()
        paragraph = self._ensure_paragraph(latex)
        if paragraph is None:
            return

        info = self.context.get("labels", {}).get(label_name)
        anchor_name = self._anchor_name(label_name)
        if info is not None:
            anchor_name = info["anchor"]
        elif self._ref_text_from_aux(label_name) is None:
            latex.append_inline(text)
            return

        with latex.render_frame(link={"anchor": anchor_name}):
            latex.append_inline(text)

    def append_external_link(self, latex, url: str, text: str):
        self._ensure_state()
        paragraph = self._ensure_paragraph(latex)
        if paragraph is None:
            return

        with latex.render_frame(link={"url": url}):
            latex.append_inline(text)


def register(latex):
    resolver = ReferenceResolver(latex.context)
    latex.reference_resolver = resolver

    for macro_name, macro_class in {
        "href": href,
        "hyperref": hyperref,
        "eqref": eqref,
        "ref": ref,
        "label": label,
    }.items():
        latex.macro(macro_name, macro_class)

    @latex.command("label", inline=True)
    def handle_label(node):
        label_name = latex.get_arg_text(node, 0, key="label")
        if not label_name:
            return
        resolver.register_label(latex, label_name)

    @latex.command("ref", inline=True)
    def handle_ref(node):
        label_name = latex.get_arg_text(node, 0, key="label")
        ref_text = resolver.resolve_ref_text(label_name)
        resolver.append_internal_link(latex, label_name, ref_text)

    @latex.command("eqref", inline=True)
    def handle_eqref(node):
        label_name = latex.get_arg_text(node, 0, key="label")
        ref_text = resolver.resolve_ref_text(label_name)
        resolver.append_internal_link(latex, label_name, f"({ref_text})")

    @latex.command("href", inline=True)
    def handle_href(node):
        url = latex.get_arg_text(node, 0, key="url")
        text_fragment = getattr(node, "attributes", {}).get("self")
        if text_fragment is not None and getattr(text_fragment, "childNodes", None):
            with latex.render_frame(link={"url": url}):
                latex.render_nodes(text_fragment.childNodes)
            return
        text = latex.get_arg_text(node, 1, key="self") or url
        resolver.append_external_link(latex, url, text)

    @latex.command("hyperref", inline=True)
    def handle_hyperref(node):
        label_name = latex.get_arg_text(node, 0, key="label")
        anchor_name = resolver.anchor_name(label_name)
        text_fragment = getattr(node, "attributes", {}).get("self")
        if text_fragment is not None and getattr(text_fragment, "childNodes", None):
            with latex.render_frame(link={"anchor": anchor_name}):
                latex.render_nodes(text_fragment.childNodes)
            return
        text = latex.get_arg_text(node, 1, key="self") or resolver.resolve_ref_text(
            label_name
        )
        resolver.append_internal_link(latex, label_name, text)

    return resolver
