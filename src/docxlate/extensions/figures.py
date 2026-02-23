from __future__ import annotations

from pathlib import Path

from docx.oxml.ns import qn
from docx.shared import Emu, Inches
from plasTeX import Command, Environment

from docxlate.docx_ext import (
    convert_inline_drawing_to_wrapped_anchor,
    insert_wrapped_caption_anchor,
)


class includegraphics(Command):
    args = "[ options ] file:str"


class caption(Command):
    args = "[ toc ] self"


class wrapfigure(Environment):
    args = "[ lines ] place:str width"


def _resolve_image_path(latex, raw_path: str) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    bases = []
    tex_path = latex.context.get("tex_path")
    if tex_path:
        bases.append(Path(tex_path).resolve().parent)
    bases.append(Path.cwd())

    for base in bases:
        p = (base / candidate).resolve()
        if p.exists():
            return p
        for ext in (".png", ".jpg", ".jpeg", ".pdf"):
            with_ext = p.with_suffix(ext)
            if with_ext.exists():
                return with_ext
    return None


def _section_textwidth_emu(latex) -> int:
    try:
        section = latex.doc.sections[-1]
        width = int(section.page_width) - int(section.left_margin) - int(section.right_margin)
        return max(width, int(Inches(4.0)))
    except Exception:
        return int(Inches(6.0))


def _parse_latex_length_inches(raw_value: str | None) -> float | None:
    if not raw_value:
        return None
    value = raw_value.strip()
    if value.endswith("in"):
        try:
            return float(value[:-2])
        except ValueError:
            return None
    if value.endswith("cm"):
        try:
            return float(value[:-2]) / 2.54
        except ValueError:
            return None
    if value.endswith("pt"):
        try:
            return float(value[:-2]) / 72.0
        except ValueError:
            return None
    return None


def _parse_textwidth_fraction_emu(raw_value: str | None, textwidth_emu: int) -> int | None:
    if not raw_value:
        return None
    value = raw_value.strip().replace(" ", "")
    if not value.endswith("\\textwidth"):
        return None
    try:
        return int(float(value[: -len("\\textwidth")]) * textwidth_emu)
    except ValueError:
        return None


def _parse_latex_length_emu(raw_value: str | None, textwidth_emu: int) -> int | None:
    if not raw_value:
        return None
    by_textwidth = _parse_textwidth_fraction_emu(raw_value, textwidth_emu)
    if by_textwidth is not None:
        return by_textwidth
    inches = _parse_latex_length_inches(raw_value)
    if inches is not None:
        return int(Inches(inches))
    return None


def _resolve_width_hint(latex, node):
    options = latex.get_arg_text(node, 0, key="options")
    width_hint = None
    if options and "width=" in options:
        for token in options.split(","):
            token = token.strip()
            if token.startswith("width="):
                width_hint = token.split("=", 1)[1].strip()
                break
    return width_hint


def _resolve_target_width_emu(latex, node, stack) -> int:
    textwidth_emu = _section_textwidth_emu(latex)
    width_hint = _resolve_width_hint(latex, node)
    if width_hint:
        parsed = _parse_latex_length_emu(width_hint, textwidth_emu)
        if parsed and parsed > 0:
            return parsed
    if stack:
        wrap_width = stack[-1].get("width")
        parsed = _parse_latex_length_emu(wrap_width, textwidth_emu)
        if parsed and parsed > 0:
            return parsed
    return int(Inches(4.5))


def _estimate_caption_box_height_emu(text: str, box_cx_emu: int) -> int:
    caption = (text or "").strip()
    if not caption:
        return 320000
    # Approximate line capacity from box width using ~5.2 pt average glyph width.
    width_pt = max(40.0, box_cx_emu / 12700.0)
    chars_per_line = max(16, int(width_pt / 5.2))
    line_count = max(1, (len(caption) + chars_per_line - 1) // chars_per_line)
    line_height_emu = int(12 * 12700)  # ~12pt
    padding = int(8 * 12700)
    return max(320000, line_count * line_height_emu + padding)


def register(latex):
    for macro_name, macro_class in {
        "includegraphics": includegraphics,
        "caption": caption,
        "wrapfigure": wrapfigure,
    }.items():
        latex.macro(macro_name, macro_class)

    @latex.command("includegraphics", inline=True)
    def handle_includegraphics(node):
        raw_path = latex.get_arg_text(node, 0, key="file")
        image_path = _resolve_image_path(latex, raw_path)
        if image_path is None:
            latex.context.setdefault("warnings", []).append(
                f"Image file not found: {raw_path}"
            )
            latex.append_inline(f"[Missing image: {raw_path}]")
            return

        paragraph = latex._active_paragraph()
        if paragraph is None:
            paragraph = latex.doc.add_paragraph()
            latex._current_paragraph = paragraph

        stack = latex.context.get("figure_stack", [])
        in_wrapfigure = bool(stack and stack[-1].get("kind") == "wrapfigure")
        place = stack[-1].get("place") if in_wrapfigure else None
        target_width_emu = _resolve_target_width_emu(latex, node, stack if in_wrapfigure else [])

        try:
            run = paragraph.add_run()
            run.add_picture(str(image_path), width=Emu(target_width_emu))
        except Exception:
            run = paragraph.add_run()
            run.add_picture(str(image_path))

        if in_wrapfigure:
            drawing = run._r.find(qn("w:drawing"))
            if drawing is not None:
                anchor = convert_inline_drawing_to_wrapped_anchor(
                    drawing, place=place, pos_y_emu=0
                )
                if anchor is not None:
                    extent = anchor.find(qn("wp:extent"))
                    if extent is not None and stack:
                        stack[-1]["image_cx_emu"] = int(extent.get("cx", "0"))
                        stack[-1]["image_cy_emu"] = int(extent.get("cy", "0"))
                        stack[-1]["target_cx_emu"] = target_width_emu

    @latex.command("caption", inline=True)
    def handle_caption(node):
        p = latex.doc.add_paragraph(style="Caption") if "Caption" in [s.name for s in latex.doc.styles if s.type == 1] else latex.doc.add_paragraph()
        stack = latex.context.get("figure_stack", [])
        self_fragment = getattr(node, "attributes", {}).get("self")
        with latex.render_frame(paragraph=p):
            if self_fragment is not None and getattr(self_fragment, "childNodes", None):
                latex.render_nodes(self_fragment.childNodes)
            else:
                text = latex.get_arg_text(node, 0, key="self")
                latex.append_inline(text)
        if stack and stack[-1].get("kind") == "wrapfigure":
            image_cx = int(stack[-1].get("image_cx_emu", 2160000))
            image_cy = int(stack[-1].get("image_cy_emu", 1000000))
            box_cx = int(stack[-1].get("target_cx_emu", image_cx))
            caption_cy = _estimate_caption_box_height_emu(p.text, box_cx)
            insert_wrapped_caption_anchor(
                latex.doc,
                source_paragraph=p,
                place=stack[-1].get("place"),
                pos_y_emu=image_cy + 114300,
                box_cx_emu=max(1200000, box_cx),
                box_cy_emu=caption_cy,
            )

    @latex.env("wrapfigure")
    def handle_wrapfigure(node):
        lines = latex.get_arg_text(node, 0, key="lines")
        place = latex.get_arg_text(node, 0, key="place")
        width = latex.get_arg_text(node, 1, key="width")
        p = latex.doc.add_paragraph()
        stack = latex.context.setdefault("figure_stack", [])
        stack.append({"kind": "wrapfigure", "place": place, "width": width, "lines": lines})
        try:
            with latex.render_frame(paragraph=p):
                latex.render_nodes(node.childNodes)
        finally:
            stack.pop()

    return None
