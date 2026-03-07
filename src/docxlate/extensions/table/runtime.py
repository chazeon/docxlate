from __future__ import annotations

import re

from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from plasTeX import Command, Environment

from docxlate.model import RenderContext
from docxlate.registry import MacroSpec


class table(Environment):
    args = "[ position ]"


class tabular(Environment):
    args = "colspec:str"


class multicolumn(Command):
    args = "cols:str align:str self"


def _node_name(node) -> str:
    node_name = getattr(node, "nodeName", None)
    return str(node_name).lstrip("\\") if node_name is not None else ""


def _split_tabular_rows(nodes: list) -> list[list[list]]:
    rows: list[list[list]] = [[]]
    current_cell: list = []

    for child in nodes:
        raw_name = getattr(child, "nodeName", None)
        if raw_name is not None and str(raw_name) == "\\":
            rows[-1].append(current_cell)
            current_cell = []
            rows.append([])
            continue
        if _node_name(child) == "active::&":
            rows[-1].append(current_cell)
            current_cell = []
            continue
        current_cell.append(child)

    rows[-1].append(current_cell)

    while rows and all(len(cell) == 0 for cell in rows[-1]):
        rows.pop()
    if not rows:
        return []
    return rows


def _alignment_tokens_from_colspec(colspec: str) -> list[str]:
    # MVP parser: recognize only simple LaTeX alignment tokens.
    return [token for token in re.findall(r"[clr]", colspec or "")]


def _alignment_for_token(token: str):
    if token == "c":
        return WD_ALIGN_PARAGRAPH.CENTER
    if token == "r":
        return WD_ALIGN_PARAGRAPH.RIGHT
    return WD_ALIGN_PARAGRAPH.LEFT


def _resolve_table_style(doc, *, candidates: list[str], fallback: str | None) -> str | None:
    table_styles = [s for s in doc.styles if s.type == WD_STYLE_TYPE.TABLE]
    if not table_styles:
        return None

    style_by_name = {s.name: s for s in table_styles}
    style_by_id = {str(s.style_id): s for s in table_styles}

    for candidate in candidates:
        style = style_by_name.get(candidate) or style_by_id.get(candidate)
        if style is not None:
            return str(style.name)

    if fallback:
        style = style_by_name.get(fallback) or style_by_id.get(fallback)
        if style is not None:
            return str(style.name)

    # deterministic final fallback: first table style in template
    return str(table_styles[0].name)


def _render_caption(latex, caption_node, *, label_names: list[str], anchor_paragraph):
    refs = latex.context.get("refs", {})
    resolved = None
    for label_name in label_names:
        info = refs.get(label_name, {})
        value = info.get("ref_num")
        if value is not None:
            resolved = str(value)
            break

    caption_ctx = RenderContext().with_para_role("caption")
    caption_para = latex.add_paragraph_for_role("caption")
    prefix = f"Table {resolved or '?'}"
    with latex.render_frame(paragraph=caption_para, style=caption_ctx):
        latex.append_inline(f"{prefix}. ", style={"bold": True, "theme": "major"})
        fragment = getattr(caption_node, "attributes", {}).get("self")
        if fragment is not None and getattr(fragment, "childNodes", None):
            latex.render_nodes(fragment.childNodes)
        else:
            text = latex.get_arg_text(caption_node, 0, key="self")
            if text:
                latex.append_inline(text)

    resolver = getattr(latex, "reference_resolver", None)
    if resolver is None:
        return
    current = latex._current_paragraph
    latex._current_paragraph = caption_para
    try:
        for label_name in label_names:
            resolver.register_label(
                latex,
                label_name,
                ref_text=resolved,
            )
    finally:
        latex._current_paragraph = current


def register(latex, *, plugin):
    def _render_tabular(node):
        rows = _split_tabular_rows(list(getattr(node, "childNodes", []) or []))
        if not rows:
            return None

        colspec = latex.get_arg_text(node, 0, key="colspec")
        align_tokens = _alignment_tokens_from_colspec(colspec)
        col_count = max(len(row) for row in rows)
        if col_count <= 0:
            return None

        latex._flush_paragraph()
        doc_table = latex.doc.add_table(rows=len(rows), cols=col_count)
        selected_style = _resolve_table_style(
            latex.doc,
            candidates=plugin.style_candidates(latex),
            fallback=plugin.fallback_style(latex),
        )
        if selected_style is not None:
            try:
                doc_table.style = selected_style
            except Exception:
                latex.context.setdefault("warnings", []).append(
                    f"Failed to apply table style: {selected_style}"
                )
        doc_table.autofit = plugin.autofit(latex)

        anchor_paragraph = None
        for row_idx, row_cells in enumerate(rows):
            for col_idx in range(col_count):
                cell = doc_table.cell(row_idx, col_idx)
                paragraph = cell.paragraphs[0]
                anchor_paragraph = paragraph
                if col_idx < len(align_tokens):
                    paragraph.alignment = _alignment_for_token(align_tokens[col_idx])
                content = row_cells[col_idx] if col_idx < len(row_cells) else []
                with latex.render_frame(paragraph=paragraph):
                    latex.render_nodes(content)
        latex._flush_paragraph()
        return anchor_paragraph

    @latex.env("tabular", parse_class=tabular)
    def handle_tabular(node):
        _render_tabular(node)

    @latex.env("table", parse_class=table)
    def handle_table(node):
        caption_node = None
        label_names: list[str] = []
        tabular_nodes: list = []
        passthrough_nodes: list = []

        for child in list(getattr(node, "childNodes", []) or []):
            name = _node_name(child)
            if name == "caption":
                caption_node = child
                continue
            if name == "label":
                label_name = latex.get_arg_text(child, 0, key="label").strip()
                if label_name:
                    label_names.append(label_name)
                continue
            if name == "tabular":
                tabular_nodes.append(child)
                continue
            passthrough_nodes.append(child)

        anchor_paragraph = None
        for tabular_node in tabular_nodes:
            rendered_anchor = _render_tabular(tabular_node)
            if rendered_anchor is not None:
                anchor_paragraph = rendered_anchor

        if caption_node is not None:
            _render_caption(
                latex,
                caption_node,
                label_names=label_names,
                anchor_paragraph=anchor_paragraph,
            )
        elif label_names:
            resolver = getattr(latex, "reference_resolver", None)
            if resolver is not None and anchor_paragraph is not None:
                current = latex._current_paragraph
                latex._current_paragraph = anchor_paragraph
                try:
                    for label_name in label_names:
                        resolver.register_label(latex, label_name)
                finally:
                    latex._current_paragraph = current

        if passthrough_nodes:
            latex.render_nodes(passthrough_nodes)

    latex.register_spec(
        MacroSpec(
            name="multicolumn",
            kind="command",
            parse_class=multicolumn,
            policy="stub",
        )
    )
    return None


__all__ = ["register"]
