from __future__ import annotations

from pathlib import Path

from docx.shared import Inches
from plasTeX import Command

from docxlate.aux import parse_abx_aux_cite_order, parse_refs
from docxlate.bbl import format_bibliography_entry, parse_bbl
from docxlate.bcf import parse_bcf


class DocxlateBibEntry(Command):
    macroName = "docxlatebibentry"
    args = "idx:str self"


BIBLIOGRAPHY_MACRO_DEFAULTS: dict[str, str] = {
    "bibinitperiod": ".",
    "bibnamedelima": " ",
    "bibinitdelim": " ",
    "bibinithyphendelim": "-",
}


def _reference_number_for_key(key: str, index: int, cite_order: dict[str, int]) -> int:
    value = cite_order.get(key)
    if value is not None:
        return int(value)
    return index + 1


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _compress_numeric_cite_items(
    items: list[tuple[str, str]],
    *,
    min_run: int,
) -> list[tuple[str | None, str]]:
    numeric: list[tuple[str, int]] = []
    for label, value in items:
        num = _parse_positive_int(value)
        if num is None:
            return [(lbl, val) for lbl, val in items]
        numeric.append((label, num))

    numeric.sort(key=lambda pair: pair[1])
    deduped: list[tuple[str, int]] = []
    seen_nums: set[int] = set()
    for label, num in numeric:
        if num in seen_nums:
            continue
        seen_nums.add(num)
        deduped.append((label, num))

    out: list[tuple[str | None, str]] = []
    i = 0
    while i < len(deduped):
        start_label, start_num = deduped[i]
        j = i
        while j + 1 < len(deduped) and deduped[j + 1][1] == deduped[j][1] + 1:
            j += 1
        run_len = j - i + 1
        if run_len >= min_run:
            out.append((start_label, f"{start_num}\u2013{deduped[j][1]}"))
        else:
            for k in range(i, j + 1):
                out.append((deduped[k][0], str(deduped[k][1])))
        i = j + 1
    return out


def register(latex, *, plugin):
    latex.macro("docxlatebibentry", DocxlateBibEntry)

    for macro_name in BIBLIOGRAPHY_MACRO_DEFAULTS:
        @latex.command(macro_name, inline=True)
        def _handle_bibliography_macro(_node, _macro_name=macro_name):
            latex.append_inline(plugin.macro_text(latex, _macro_name))

    @latex.command("cite", inline=True)
    def handle_cite(node):
        cite_order = latex.context.get("cite_order", {})
        refs = latex.context.get("refs", {})
        bib_links = latex.context.get("bib_entry_labels", {})
        bbl_entries = latex.context.get("bbl_entries", {})
        resolver = getattr(latex, "reference_resolver", None)

        label_text = latex.get_arg_text(node, 0, key="bibkeys")
        labels = [lbl.strip() for lbl in label_text.split(",") if lbl.strip()]
        resolved: list[tuple[str, str]] = []
        for label in labels:
            ref_num = cite_order.get(label)
            if ref_num is None:
                ref_info = refs.get(label, {})
                ref_num = ref_info.get("ref_num")
            resolved.append((label, str(ref_num) if ref_num is not None else label))

        seen_values: set[str] = set()
        unique_resolved: list[tuple[str, str]] = []
        for label, value in resolved:
            if value in seen_values:
                continue
            seen_values.add(value)
            unique_resolved.append((label, value))

        citation = plugin.citation_settings(latex)
        compress_ranges = bool(citation["compress_ranges"])
        min_run = int(citation["min_run"])
        cite_items: list[tuple[str | None, str]]
        if compress_ranges:
            cite_items = _compress_numeric_cite_items(unique_resolved, min_run=min_run)
        else:
            cite_items = [(label, value) for label, value in unique_resolved]

        latex.append_inline("[")
        for idx, (label, value) in enumerate(cite_items):
            if idx:
                latex.append_inline(",")
            target_label = None
            if label is not None:
                target_label = bib_links.get(label)
                if target_label is None and label in bbl_entries:
                    target_label = f"bib:{label}"
            if resolver is not None and target_label:
                with latex.render_frame(link={"anchor": resolver.anchor_name(target_label)}):
                    latex.append_inline(value)
            else:
                latex.append_inline(value)
        latex.append_inline("]")

    @latex.command("docxlatebibentry", inline=True)
    def handle_docxlate_bib_entry(node):
        idx_text = latex.get_arg_text(node, 0, key="idx")
        try:
            idx = int(idx_text)
        except (TypeError, ValueError):
            return

        ordered_keys = latex.context.get("_bib_render_order", [])
        if idx < 0 or idx >= len(ordered_keys):
            return
        key = ordered_keys[idx]
        cite_order = latex.context.get("_bib_render_cite_order", {})
        layout = latex.context.get("_bib_render_layout") or plugin.layout_settings(latex)

        p = latex.add_paragraph_for_role("bibliography")
        if layout["numbering"] == "bracket":
            indent = Inches(float(layout["indent_in"]))
            p.paragraph_format.left_indent = indent
            p.paragraph_format.first_line_indent = -indent
            p.paragraph_format.tab_stops.add_tab_stop(indent)
            ref_num = _reference_number_for_key(key, idx, cite_order)
            p.add_run(f"[{ref_num}]\t")

        text_fragment = getattr(node, "attributes", {}).get("self")
        if text_fragment is not None and getattr(text_fragment, "childNodes", None):
            with latex.render_frame(paragraph=p):
                latex.render_nodes(text_fragment.childNodes)

        resolver = getattr(latex, "reference_resolver", None)
        if resolver is not None:
            label_name = f"bib:{key}"
            current = latex._current_paragraph
            latex._current_paragraph = p
            resolver.register_label(latex, label_name)
            latex._current_paragraph = current
            latex.context.setdefault("bib_entry_labels", {})[key] = label_name

    @latex.on("load")
    def on_load(_tex_source, _soup):
        tex_path = latex.context.get("tex_path")
        if not tex_path:
            return
        latex.context["bibcites"] = {}
        latex.context["cite_order"] = {}
        latex.context["bbl_entries"] = {}
        latex.context["bib_entry_labels"] = {}
        aux_path = Path(tex_path).with_suffix(".aux")
        if aux_path.exists():
            _refs, bibcites = parse_refs(aux_path)
            latex.context["bibcites"] = bibcites
            latex.context["cite_order"] = parse_abx_aux_cite_order(aux_path)
        bcf_path = Path(tex_path).with_suffix(".bcf")
        if bcf_path.exists() and not latex.context.get("cite_order"):
            latex.context["cite_order"] = parse_bcf(bcf_path)
        bbl_path = Path(tex_path).with_suffix(".bbl")
        if bbl_path.exists():
            latex.context["bbl_entries"] = parse_bbl(bbl_path)

    @latex.on("post_process")
    def append_references():
        entries = latex.context.get("bbl_entries", {})
        if not entries:
            return

        cite_order = latex.context.get("cite_order", {})
        if cite_order:
            ordered_keys = [
                k
                for k, _ in sorted(cite_order.items(), key=lambda item: item[1])
                if k in entries
            ]
        else:
            ordered_keys = sorted(entries.keys())
        if not ordered_keys:
            return

        heading = latex.add_paragraph_for_role("references_heading")
        with latex.render_frame(paragraph=heading):
            latex.append_inline("References", style={"bold": True, "theme": "major"})
        latex.mark_next_body_paragraph_first()
        latex.context["bib_entry_labels"] = {}
        layout = plugin.layout_settings(latex)
        bib_template = plugin.template(latex)
        et_al_limit = plugin.et_al_limit(latex)

        chunks: list[str] = []
        for index, key in enumerate(ordered_keys):
            text = format_bibliography_entry(
                entries[key],
                template=bib_template,
                et_al_limit=et_al_limit,
            )
            chunks.append(rf"\docxlatebibentry{{{index}}}{{{text}}}")

        latex.context["_bib_render_order"] = ordered_keys
        latex.context["_bib_render_layout"] = layout
        latex.context["_bib_render_cite_order"] = cite_order
        try:
            latex.render_latex_fragment("\n".join(chunks))
        finally:
            latex.context.pop("_bib_render_order", None)
            latex.context.pop("_bib_render_layout", None)
            latex.context.pop("_bib_render_cite_order", None)

    return None


__all__ = ["BIBLIOGRAPHY_MACRO_DEFAULTS", "register"]
