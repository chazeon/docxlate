from __future__ import annotations


def estimate_caption_box_height_emu(text: str, box_cx_emu: int) -> int:
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


__all__ = ["estimate_caption_box_height_emu"]
