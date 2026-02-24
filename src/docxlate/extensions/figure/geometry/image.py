from __future__ import annotations

from pathlib import Path

from docx.shared import Inches


def resolve_image_path(latex, raw_path: str) -> Path | None:
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


def section_textwidth_emu(latex) -> int:
    try:
        section = latex.doc.sections[-1]
        width = int(section.page_width) - int(section.left_margin) - int(section.right_margin)
        return max(width, int(Inches(4.0)))
    except Exception:
        return int(Inches(6.0))


def parse_latex_length_inches(raw_value: str | None) -> float | None:
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


def parse_textwidth_fraction_emu(raw_value: str | None, textwidth_emu: int) -> int | None:
    if not raw_value:
        return None
    value = raw_value.strip().replace(" ", "")
    if not value.endswith("\\textwidth"):
        return None
    try:
        return int(float(value[: -len("\\textwidth")]) * textwidth_emu)
    except ValueError:
        return None


def parse_latex_length_emu(raw_value: str | None, textwidth_emu: int) -> int | None:
    if not raw_value:
        return None
    by_textwidth = parse_textwidth_fraction_emu(raw_value, textwidth_emu)
    if by_textwidth is not None:
        return by_textwidth
    inches = parse_latex_length_inches(raw_value)
    if inches is not None:
        return int(Inches(inches))
    return None


def resolve_width_hint(latex, node):
    options = latex.get_arg_text(node, 0, key="options")
    width_hint = None
    if options and "width=" in options:
        for token in options.split(","):
            token = token.strip()
            if token.startswith("width="):
                width_hint = token.split("=", 1)[1].strip()
                break
    return width_hint


def resolve_target_width_emu(latex, node, stack) -> int:
    textwidth_emu = section_textwidth_emu(latex)
    width_hint = resolve_width_hint(latex, node)
    if width_hint:
        parsed = parse_latex_length_emu(width_hint, textwidth_emu)
        if parsed and parsed > 0:
            return parsed
    if stack:
        wrap_width = stack[-1].get("width")
        parsed = parse_latex_length_emu(wrap_width, textwidth_emu)
        if parsed and parsed > 0:
            return parsed
    return int(Inches(4.5))


__all__ = [
    "parse_latex_length_emu",
    "parse_latex_length_inches",
    "parse_textwidth_fraction_emu",
    "resolve_image_path",
    "resolve_target_width_emu",
    "resolve_width_hint",
    "section_textwidth_emu",
]
