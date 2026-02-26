from __future__ import annotations


def wrapped_figure_box_size(stack_entry: dict, caption_cy: int, gap_emu: int) -> tuple[int, int]:
    image_cx = int(stack_entry.get("image_cx_emu", 2160000))
    image_cy = int(stack_entry.get("image_cy_emu", 1000000))
    box_cx = max(image_cx, int(stack_entry.get("target_cx_emu", image_cx)))
    box_cy = max(320000, image_cy + gap_emu + caption_cy)
    return max(1200000, box_cx), box_cy


__all__ = ["wrapped_figure_box_size"]
