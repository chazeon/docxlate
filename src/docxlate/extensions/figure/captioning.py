from __future__ import annotations

from jinja2 import Environment as JinjaEnvironment

def caption_template_env() -> JinjaEnvironment:
    return JinjaEnvironment(
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
    )


def caption_template_source(template: str) -> str:
    source = template
    # Allow simple {{ var }} placeholders as a compatibility shorthand.
    if "{{" in source and "<<" not in source:
        source = source.replace("{{", "<<").replace("}}", ">>")
    return source


def caption_tex_from_node(latex, node) -> str:
    fragment = getattr(node, "attributes", {}).get("self")
    source = getattr(fragment, "source", None) if fragment is not None else None
    if source is not None and str(source).strip():
        return str(source).strip()
    return latex.get_arg_text(node, 0, key="self")


def fragment_text(value) -> str | None:
    if value is None:
        return None
    text_content = getattr(value, "textContent", None)
    if text_content is not None:
        text = str(text_content).strip()
        if text:
            return text
    source = getattr(value, "source", None)
    if source is not None:
        text = str(source).strip()
        if text:
            return text
    text = str(value).strip()
    if text and "plasTeX.TeXFragment object" not in text:
        return text
    return None


def find_figure_label(latex, node) -> str | None:
    scope = getattr(node, "parentNode", None)
    while scope is not None:
        stack = list(getattr(scope, "childNodes", []) or [])
        while stack:
            child = stack.pop(0)
            if getattr(child, "nodeName", None) == "label":
                label_name = latex.get_arg_text(child, 0, key="label")
                if label_name:
                    return label_name
            stack[0:0] = list(getattr(child, "childNodes", []) or [])
        node_name = getattr(scope, "nodeName", None)
        if node_name in {"figure", "wrapfigure"}:
            break
        scope = getattr(scope, "parentNode", None)
    return None


def resolved_label_number(latex, label_name: str | None) -> str:
    if not label_name:
        return "?"
    refs = latex.context.get("refs", {})
    ref_info = refs.get(label_name, {})
    ref_text = ref_info.get("ref_num")
    if ref_text is not None:
        return str(ref_text)
    labels = latex.context.get("labels", {})
    known = labels.get(label_name, {})
    known_text = known.get("ref_text")
    if known_text:
        return str(known_text)
    return "?"


def figure_name_from_node(node) -> str:
    name = fragment_text(getattr(node, "captionName", None))
    if name and "\\" not in name and "{" not in name and "}" not in name:
        return name
    return "Figure"


def figure_number_from_node(node) -> str | None:
    value = fragment_text(getattr(node, "ref", None))
    if not value:
        return None
    if "\\" in value or "{" in value or "}" in value:
        return None
    return value


def render_caption_with_template(latex, node, *, plugin) -> str | None:
    figure_cfg = plugin.figure_config(latex)
    caption_cfg = figure_cfg.get("caption") if isinstance(figure_cfg, dict) else None
    template = caption_cfg.get("template") if isinstance(caption_cfg, dict) else None
    if not template:
        return None
    slot = "__DOCXLATE_CAPTION_SLOT__"
    label_name = find_figure_label(latex, node)
    fig_num = resolved_label_number(latex, label_name)
    if fig_num == "?":
        parsed_ref = figure_number_from_node(node)
        if parsed_ref:
            fig_num = parsed_ref
    fig_name = figure_name_from_node(node)
    env = caption_template_env()
    compiled = env.from_string(caption_template_source(str(template)))
    return compiled.render(
        x=fig_num,
        number=fig_num,
        fig_num=fig_num,
        thefigure=fig_num,
        fig_name=fig_name,
        figurename=fig_name,
        caption=slot,
        caption_tex=slot,
        label=label_name or "",
    ).strip()


__all__ = [
    "caption_tex_from_node",
    "caption_template_env",
    "caption_template_source",
    "figure_name_from_node",
    "figure_number_from_node",
    "find_figure_label",
    "fragment_text",
    "render_caption_with_template",
    "resolved_label_number",
]
