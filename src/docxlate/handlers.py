from .core import LatexBridge
from .utils import apply_theme_font, inject_omml
from .aux import parse_abx_aux_cite_order, parse_refs
from .bbl import format_bibliography_entry, parse_bbl
from .bcf import parse_bcf
from .extensions import (
    register_figures_extension,
    register_hyperref_extension,
    register_lists_extension,
)
from pathlib import Path
from docx.shared import Pt, Inches
import re
from plasTeX import Command

latex = LatexBridge()
register_hyperref_extension(latex)
register_lists_extension(latex)
register_figures_extension(latex)


class And(Command):
    macroName = "and"
    args = ""


latex.macro("and", And)


def _bibliography_layout_settings() -> dict:
    """
    Reference list layout configuration from context.
    Supported keys:
    - bibliography_numbering: "bracket" (default) or "none"
    - bibliography_indent_in: float inches for hanging indent block (default 0.35)
    """
    numbering = str(latex.context.get("bibliography_numbering", "bracket")).lower()
    if numbering not in {"bracket", "none"}:
        numbering = "bracket"
    try:
        indent_in = float(latex.context.get("bibliography_indent_in", 0.35))
    except (TypeError, ValueError):
        indent_in = 0.35
    if indent_in <= 0:
        indent_in = 0.35
    return {"numbering": numbering, "indent_in": indent_in}


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


def _math_node_text(node):
    return latex.get_math_source(node)


def _store_front_matter_tex(node, key: str):
    attributes = getattr(node, "attributes", {}) or {}
    fragment = attributes.get("self")
    source = getattr(fragment, "source", None) if fragment is not None else None
    if source is None:
        source = latex.get_arg_text(node, 0, key="self")
    text = str(source).strip() if source is not None else ""
    if text:
        latex.context[f"_frontmatter_{key}_tex"] = text


def _extract_preamble(tex_source: str) -> str:
    marker = r"\begin{document}"
    idx = tex_source.find(marker)
    if idx == -1:
        return tex_source
    return tex_source[:idx]


def _read_balanced_braces(text: str, start_idx: int) -> tuple[str, int]:
    if start_idx >= len(text) or text[start_idx] != "{":
        return "", start_idx
    depth = 0
    i = start_idx + 1
    out: list[str] = []
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            out.append(ch)
            out.append(text[i + 1])
            i += 2
            continue
        if ch == "{":
            depth += 1
            out.append(ch)
            i += 1
            continue
        if ch == "}":
            if depth == 0:
                return "".join(out), i + 1
            depth -= 1
            out.append(ch)
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out), i


def _extract_last_braced_command_argument(source: str, command_name: str) -> str | None:
    # Keep escaped percent signs, strip true comments.
    cleaned = re.sub(r"(?<!\\)%.*", "", source)
    pattern = re.compile(rf"(?<!\\)\\{re.escape(command_name)}\b")
    last_value: str | None = None
    pos = 0
    while True:
        match = pattern.search(cleaned, pos)
        if not match:
            break
        i = match.end()
        while i < len(cleaned) and cleaned[i].isspace():
            i += 1
        if i < len(cleaned) and cleaned[i] == "{":
            value, nxt = _read_balanced_braces(cleaned, i)
            if value.strip():
                last_value = value.strip()
            else:
                last_value = ""
            pos = max(nxt, match.end() + 1)
            continue
        pos = match.end() + 1
    return last_value


def _populate_front_matter_from_source(tex_source: str):
    preamble = _extract_preamble(tex_source)
    for key in ("title", "author", "date"):
        context_key = f"_frontmatter_{key}_tex"
        if latex.context.get(context_key):
            continue
        value = _extract_last_braced_command_argument(preamble, key)
        if value is not None:
            latex.context[context_key] = value


def _normalized_title_policy() -> str:
    raw = str(latex.context.get("title_render_policy", "auto")).lower()
    if raw in {"explicit", "auto", "always"}:
        return raw
    return "auto"


def _front_matter_has_content() -> bool:
    return any(
        latex.context.get(k)
        for k in (
            "_frontmatter_title_tex",
            "_frontmatter_author_tex",
            "_frontmatter_date_tex",
        )
    )


def _used_body_only_parse_fallback() -> bool:
    warnings = latex.context.get("warnings", [])
    return any("body-only parse fallback" in w for w in warnings)


def _prepend_paragraphs(paragraphs):
    body = latex.doc._element.body
    nodes = [p._p for p in paragraphs if p is not None]
    if not nodes:
        return
    for node in nodes:
        body.remove(node)
    first_idx = 0
    for i, child in enumerate(list(body)):
        if child.tag.endswith("}sectPr"):
            continue
        first_idx = i
        break
    for offset, node in enumerate(nodes):
        body.insert(first_idx + offset, node)


def _emit_front_matter(*, prepend: bool = False):
    if latex.context.get("_frontmatter_rendered"):
        return
    title_tex = latex.context.get("_frontmatter_title_tex")
    author_tex = latex.context.get("_frontmatter_author_tex")
    date_tex = latex.context.get("_frontmatter_date_tex")
    if not any([title_tex, author_tex, date_tex]):
        return

    created = []
    if title_tex:
        p_title = latex.add_paragraph_for_role("title")
        latex.render_latex_fragment(
            title_tex, paragraph=p_title, style={"theme": "major"}
        )
        created.append(p_title)

    if author_tex:
        p_author = latex.add_paragraph_for_role("author")
        latex.context["_in_maketitle_author"] = True
        try:
            latex.render_latex_fragment(
                author_tex, paragraph=p_author, style={"theme": "major"}
            )
        finally:
            latex.context["_in_maketitle_author"] = False
        created.append(p_author)

    if date_tex:
        p_date = latex.add_paragraph_for_role("date")
        latex.render_latex_fragment(date_tex, paragraph=p_date)
        created.append(p_date)

    if prepend and created:
        _prepend_paragraphs(created)

    latex.context["_frontmatter_rendered"] = True
    latex.mark_next_body_paragraph_first()


def _handle_section(node):
    cmd = latex.get_node_name(node)
    levels: dict[str, int] = {
        "section": 1,
        "subsection": 2,
        "subsubsection": 3,
    }
    level = levels.get(cmd, 1)
    h = latex.doc.add_heading("", level=level)
    title_node = getattr(node, "attributes", {}).get("title")
    if title_node is not None and getattr(title_node, "childNodes", None):
        with latex.render_frame(paragraph=h):
            latex.render_nodes(title_node.childNodes, style={"theme": "major"})
    else:
        title = latex.get_arg_text(node, 0, key="title")
        run = h.add_run(title)
        apply_theme_font(run, "major")
    latex.mark_next_body_paragraph_first()


@latex.command("section")
def handle_section(node):
    _handle_section(node)


@latex.command("subsection")
def handle_subsection(node):
    _handle_section(node)


@latex.command("subsubsection")
def handle_subsubsection(node):
    _handle_section(node)


@latex.command("title", inline=True)
def handle_title(node):
    _store_front_matter_tex(node, "title")


@latex.command("author", inline=True)
def handle_author(node):
    _store_front_matter_tex(node, "author")


@latex.command("date", inline=True)
def handle_date(node):
    _store_front_matter_tex(node, "date")


@latex.command("and", inline=True)
def handle_and(_node):
    if latex.context.get("_in_maketitle_author"):
        paragraph = latex._active_paragraph()
        if paragraph is not None and paragraph.runs:
            paragraph.runs[-1].text = paragraph.runs[-1].text.rstrip()
        latex.append_inline(", ")
        latex.context["_trim_next_leading_space_once"] = True
    else:
        latex.append_inline(" and ")


@latex.command("maketitle")
def handle_maketitle(_node):
    latex.context["_frontmatter_maketitle_seen"] = True
    _emit_front_matter(prepend=False)


@latex.command("paragraph", inline=True)
def handle_paragraph(node):
    """Render LaTeX \\paragraph as a run-in heading."""
    current = latex._active_paragraph()
    if current is not None and any(run.text.strip() for run in current.runs):
        latex._flush_paragraph()
    latex._ensure_paragraph()
    paragraph = latex._active_paragraph()
    if paragraph is not None:
        # Keep run-in headings flush-left regardless of template body indent.
        paragraph.paragraph_format.first_line_indent = Pt(0)
        paragraph.paragraph_format.left_indent = Pt(0)

    title_node = getattr(node, "attributes", {}).get("title")
    with latex.render_frame():
        if title_node is not None and getattr(title_node, "childNodes", None):
            latex.render_nodes(
                title_node.childNodes,
                style={"bold": True, "theme": "major"},
            )
        else:
            title = latex.get_arg_text(node, 0, key="title")
            latex.append_inline(title, style={"bold": True, "theme": "major"})
        latex.append_inline(" ", style={"bold": True, "theme": "major"})
        latex.context["_preserve_paragraph_once"] = True
        latex.render_nodes(node.childNodes)


@latex.env("equation")
def handle_math(node):
    p = latex.doc.add_paragraph()
    source = latex.get_math_source(node)
    resolver = getattr(latex, "reference_resolver", None)
    refs = latex.context.get("refs", {})
    resolved_number: str | None = None
    for label_name in re.findall(r"\\label\{([^}]+)\}", source):
        ref_info = refs.get(label_name, {})
        ref_text = ref_info.get("ref_num")
        if resolved_number is None and ref_text is not None:
            resolved_number = str(ref_text)
        if resolver is not None:
            current_paragraph = latex._current_paragraph
            latex._current_paragraph = p
            resolver.register_label(
                latex, label_name, ref_text=str(ref_text) if ref_text is not None else None
            )
            latex._current_paragraph = current_paragraph
    source = re.sub(r"\\label\{[^}]+\}", "", source).strip()
    latex.emit_equation(source, number=resolved_number, paragraph=p)


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
    # Keep cite output readable even if upstream mapping contains collisions.
    seen_values: set[str] = set()
    unique_resolved: list[tuple[str, str]] = []
    for label, value in resolved:
        if value in seen_values:
            continue
        seen_values.add(value)
        unique_resolved.append((label, value))
    compress_ranges = bool(latex.context.get("citation_compress_ranges", False))
    try:
        min_run = int(latex.context.get("citation_range_min_run", 2))
    except (TypeError, ValueError):
        min_run = 2
    if min_run < 2:
        min_run = 2
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


@latex.on("load")
def on_load(tex_source, soup):
    """Parse .aux data for citation handling when available."""
    _populate_front_matter_from_source(tex_source)
    tex_path = latex.context.get("tex_path")
    if not tex_path:
        return
    latex.context["refs"] = {}
    latex.context["bibcites"] = {}
    latex.context["cite_order"] = {}
    latex.context["bbl_entries"] = {}
    latex.context["bib_entry_labels"] = {}
    latex.context["_frontmatter_rendered"] = False
    latex.context["_frontmatter_maketitle_seen"] = False
    aux_path = Path(tex_path).with_suffix(".aux")
    if aux_path.exists():
        refs, bibcites = parse_refs(aux_path)
        latex.context["refs"] = refs
        latex.context["bibcites"] = bibcites
        # Prefer biblatex AUX cite stream order; BCF order values can collide.
        latex.context["cite_order"] = parse_abx_aux_cite_order(aux_path)
    bcf_path = Path(tex_path).with_suffix(".bcf")
    if bcf_path.exists() and not latex.context.get("cite_order"):
        latex.context["cite_order"] = parse_bcf(bcf_path)
    bbl_path = Path(tex_path).with_suffix(".bbl")
    if bbl_path.exists():
        latex.context["bbl_entries"] = parse_bbl(bbl_path)


@latex.on("post_process")
def render_implicit_front_matter():
    if (
        latex.context.get("_frontmatter_maketitle_seen")
        and not _front_matter_has_content()
        and _used_body_only_parse_fallback()
    ):
        warnings = latex.context.setdefault("warnings", [])
        msg = (
            "maketitle was found, but title/author/date metadata was unavailable "
            "after body-only parse fallback; front matter was not rendered."
        )
        if msg not in warnings:
            warnings.append(msg)

    if latex.context.get("_frontmatter_rendered"):
        return
    if not _front_matter_has_content():
        return
    policy = _normalized_title_policy()
    if policy == "explicit":
        return
    # If maketitle was present, front matter should already be emitted in-place.
    if latex.context.get("_frontmatter_maketitle_seen"):
        return
    # Auto/always: emit once at document start when maketitle is absent.
    _emit_front_matter(prepend=True)


@latex.on("post_process")
def append_references():
    entries = latex.context.get("bbl_entries", {})
    if not entries:
        return

    cite_order = latex.context.get("cite_order", {})
    if cite_order:
        ordered_keys = [k for k, _ in sorted(cite_order.items(), key=lambda item: item[1]) if k in entries]
    else:
        ordered_keys = sorted(entries.keys())
    if not ordered_keys:
        return

    heading = latex.add_paragraph_for_role("references_heading")
    with latex.render_frame(paragraph=heading):
        latex.append_inline("References", style={"bold": True, "theme": "major"})
    latex.mark_next_body_paragraph_first()
    resolver = getattr(latex, "reference_resolver", None)
    latex.context["bib_entry_labels"] = {}
    layout = _bibliography_layout_settings()

    for index, key in enumerate(ordered_keys):
        bib_template = latex.context.get("bibliography_template")
        try:
            et_al_limit = int(latex.context.get("bibliography_et_al_limit", 3))
        except (TypeError, ValueError):
            et_al_limit = 3
        text = format_bibliography_entry(
            entries[key],
            template=bib_template,
            et_al_limit=et_al_limit,
        )
        p = latex.add_paragraph_for_role("bibliography")
        if layout["numbering"] == "bracket":
            indent = Inches(layout["indent_in"])
            p.paragraph_format.left_indent = indent
            p.paragraph_format.first_line_indent = -indent
            p.paragraph_format.tab_stops.add_tab_stop(indent)
            ref_num = _reference_number_for_key(key, index, cite_order)
            p.add_run(f"[{ref_num}]\t")
        latex.render_latex_fragment(text, paragraph=p)
        if resolver is not None:
            label_name = f"bib:{key}"
            current = latex._current_paragraph
            latex._current_paragraph = p
            resolver.register_label(latex, label_name)
            latex._current_paragraph = current
            latex.context["bib_entry_labels"][key] = label_name


@latex.command("$", inline=True)
def handle_inline_dollar_math(node):
    latex.append_math(_math_node_text(node))


@latex.command("math", inline=True)
def handle_inline_paren_math(node):
    latex.append_math(_math_node_text(node))
