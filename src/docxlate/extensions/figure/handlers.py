from __future__ import annotations

from docx.oxml.ns import qn
from docx.shared import Pt

from docxlate.model import RenderContext

from .captioning import render_caption_with_template
from .geometry.image import resolve_image_path, resolve_target_width_emu
from .geometry.wrap import wrapped_figure_box_size
from .layout.anchor_host import trim_trailing_whitespace_runs
from .layout.caption_box import estimate_caption_box_height_emu


def register_handlers(latex, *, plugin):
    @latex.command("includegraphics", inline=True)
    def handle_includegraphics(node):
        raw_path = latex.get_arg_text(node, 0, key="file")
        image_path = resolve_image_path(latex, raw_path)
        if image_path is None:
            latex.context.setdefault("warnings", []).append(
                f"Image file not found: {raw_path}"
            )
            latex.append_inline(f"[Missing image: {raw_path}]")
            return

        paragraph = latex._active_paragraph()
        if paragraph is None:
            latex._ensure_paragraph()
            paragraph = latex._active_paragraph()
        if paragraph is None:
            return

        stack = latex.context.get("figure_stack", [])
        in_wrapfigure = bool(stack and stack[-1].get("kind") == "wrapfigure")
        target_width_emu = resolve_target_width_emu(latex, node, stack if in_wrapfigure else [])

        try:
            run = latex.emit_image(paragraph, str(image_path), width_emu=target_width_emu)
        except Exception:
            run = latex.emit_image(paragraph, str(image_path))

        if in_wrapfigure:
            drawing = run._r.find(qn("w:drawing"))
            inline = drawing.find(qn("wp:inline")) if drawing is not None else None
            extent = inline.find(qn("wp:extent")) if inline is not None else None
            if extent is not None and stack:
                rendered_cx = int(extent.get("cx", "0"))
                rendered_cy = int(extent.get("cy", "0"))
                stack[-1]["image_run"] = run
                stack[-1]["image_cx_emu"] = rendered_cx
                stack[-1]["image_cy_emu"] = rendered_cy
                # Keep group width synced with actual rendered picture width.
                stack[-1]["target_cx_emu"] = rendered_cx if rendered_cx > 0 else target_width_emu

    @latex.command("caption", inline=True)
    def handle_caption(node):
        stack = latex.context.get("figure_stack", [])
        caption_ctx = RenderContext().with_para_role("caption")
        p = latex.add_paragraph_for_role("caption")
        templated = render_caption_with_template(latex, node, plugin=plugin)
        if templated is not None:
            slot = "__DOCXLATE_CAPTION_SLOT__"
            self_fragment = getattr(node, "attributes", {}).get("self")
            prefix, sep, suffix = templated.partition(slot)
            if prefix:
                latex.render_latex_fragment(prefix, paragraph=p, style=caption_ctx)
            with latex.render_frame(paragraph=p, style=caption_ctx):
                if self_fragment is not None and getattr(self_fragment, "childNodes", None):
                    latex.render_nodes(self_fragment.childNodes)
                else:
                    text = latex.get_arg_text(node, 0, key="self")
                    latex.append_inline(text)
            if sep and suffix:
                latex.render_latex_fragment(suffix, paragraph=p, style=caption_ctx)
        else:
            self_fragment = getattr(node, "attributes", {}).get("self")
            with latex.render_frame(paragraph=p, style=caption_ctx):
                if self_fragment is not None and getattr(self_fragment, "childNodes", None):
                    latex.render_nodes(self_fragment.childNodes)
                else:
                    text = latex.get_arg_text(node, 0, key="self")
                    latex.append_inline(text)

        if stack and stack[-1].get("kind") == "wrapfigure":
            image_run = stack[-1].get("image_run")
            gap_emu = plugin.caption_gap_emu(latex)
            box_cx, _ = wrapped_figure_box_size(stack[-1], caption_cy=0, gap_emu=gap_emu)
            caption_cy = estimate_caption_box_height_emu(p.text, box_cx)
            box_cx, box_cy = wrapped_figure_box_size(stack[-1], caption_cy=caption_cy, gap_emu=gap_emu)
            image_cy = int(stack[-1].get("image_cy_emu", 1000000))

            if image_run is not None:
                latex.emit_wrapped_figure_caption_group_anchor(
                    image_run=image_run,
                    caption_paragraph=p,
                    anchor_paragraph=stack[-1].get("anchor_paragraph"),
                    place=stack[-1].get("place"),
                    pos_y_emu=plugin.wrap_offset_y_emu(latex),
                    box_cx_emu=box_cx,
                    box_cy_emu=box_cy,
                    gap_emu=gap_emu,
                )
                stack[-1]["wrapped_emitted"] = True
            else:
                latex.emit_wrapped_caption_anchor(
                    source_paragraph=p,
                    anchor_paragraph=stack[-1].get("anchor_paragraph"),
                    place=stack[-1].get("place"),
                    pos_y_emu=plugin.wrap_offset_y_emu(latex) + image_cy + gap_emu,
                    box_cx_emu=box_cx,
                    box_cy_emu=caption_cy,
                )
                stack[-1]["wrapped_emitted"] = True

    @latex.env("wrapfigure")
    def handle_wrapfigure(node):
        lines = latex.get_arg_text(node, 0, key="lines")
        place = latex.get_arg_text(node, 0, key="place")
        width = latex.get_arg_text(node, 1, key="width")
        created_anchor_host = False
        if latex.doc.paragraphs:
            p = latex.doc.paragraphs[-1]
        else:
            p = latex.add_paragraph_for_role("body")
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            created_anchor_host = True
        stack = latex.context.setdefault("figure_stack", [])
        stack.append(
            {
                "kind": "wrapfigure",
                "place": place,
                "width": width,
                "lines": lines,
                "anchor_paragraph": p,
            }
        )
        try:
            previous_suppress = bool(latex.context.get("_suppress_whitespace_text", False))
            latex.context["_suppress_whitespace_text"] = True
            try:
                with latex.render_frame(paragraph=p):
                    latex.render_nodes(node.childNodes)
            finally:
                latex.context["_suppress_whitespace_text"] = previous_suppress
            if stack and stack[-1].get("kind") == "wrapfigure":
                image_run = stack[-1].get("image_run")
                if image_run is not None and not stack[-1].get("wrapped_emitted"):
                    anchor = latex.convert_image_run_to_wrap_anchor(
                        image_run,
                        place=stack[-1].get("place"),
                        pos_y_emu=plugin.wrap_offset_y_emu(latex),
                    )
                    if anchor is not None:
                        stack[-1]["wrapped_emitted"] = True
            trim_trailing_whitespace_runs(p)
            if created_anchor_host:
                # If wrapfigure appears at the top before any body text exists,
                # reuse this host for the immediate following paragraph content.
                latex._current_paragraph = p
                latex.context["_skip_next_par_break_once"] = True
                latex.context["_preserve_paragraph_after_env_once"] = True
        finally:
            stack.pop()

    return None


__all__ = ["register_handlers"]
