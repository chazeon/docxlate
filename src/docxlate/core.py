from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
import re

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from plasTeX import Command, Environment
from plasTeX.DOM import Text

from .utils import apply_theme_font, inject_omml


class LatexBridge:
    def __init__(self, template_path=None):
        self.doc = Document(template_path) if template_path else Document()
        self.command_handlers = {}
        self.env_handlers = {}
        self.aux_data = {}
        self.event_handlers: dict[str, list] = defaultdict(list)
        self.macro_handlers: dict[str, type] = {}
        self.context: dict = {}  # For storing state across handlers/events
        self._current_paragraph = None
        self._render_stack: list[dict] = []
        self.style_table = {
            "title": ["Title", "Heading 1", "Normal"],
            "author": ["Author", "Subtitle", "Normal"],
            "date": ["Date", "Subtitle", "Normal"],
            "first_body": [
                "FirstParagraph",
                "First Paragraph",
                "BodyText",
                "Body Text",
                "Normal",
            ],
            "body": ["BodyText", "Body Text", "Normal"],
            "references_heading": [
                "ReferencesHeading",
                "References Heading",
                "Bibliography Heading",
                "Heading1",
                "Heading 1",
            ],
            "bibliography": [
                "Bibliography",
                "References",
                "Reference",
                "BodyText",
                "Body Text",
                "Normal",
            ],
        }
        self._next_body_role = "first_body"
        self._inline_styles = {
            "textbf": {"bold": True},
            "textit": {"italic": True},
            "emph": {"italic": True},
            "textsc": {"small_caps": True},
            "texttt": {"monospace": True},
        }
        self._declaration_styles = {
            "bfseries": {"bold": True},
            "itshape": {"italic": True},
            "scshape": {"small_caps": True},
            "ttfamily": {"monospace": True},
            "upshape": {"italic": False},
            "mdseries": {"bold": False},
            "normalfont": {
                "bold": False,
                "italic": False,
                "small_caps": False,
                "monospace": False,
            },
        }

    def reset_document(self, template_path=None, *, keep_template_content=False):
        self.doc = Document(template_path) if template_path else Document()
        if template_path and not keep_template_content:
            self._clear_main_content()
        self._current_paragraph = None
        self._next_body_role = "first_body"

    def _clear_main_content(self):
        body = self.doc._element.body
        for child in list(body):
            # Keep section properties from the template; remove existing content.
            if child.tag.endswith("}sectPr"):
                continue
            body.remove(child)

    def command(self, name, *, inline=False):
        """Decorator: @app.command('section')"""

        def decorator(f):
            self.command_handlers[name] = (f, inline)
            return f

        return decorator

    def env(self, name):
        """Decorator: @app.env('equation')"""

        def decorator(f):
            self.env_handlers[name] = f
            return f

        return decorator

    def on(self, event_name):
        """Decorator: @app.on('post_process')"""

        def decorator(f):
            self.event_handlers[event_name].append(f)
            return f

        return decorator

    def macro(self, name, macro_class):
        """Register a plasTeX macro class for parse-time argument handling."""
        self.macro_handlers[name] = macro_class

    def handle_event(self, event_name, *args, **kwargs):
        """Trigger an event handler if it exists."""
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                handler(*args, **kwargs)

    def run(self, tex_source, aux_path=None):
        """The 'app.run()' equivalent: Process the document."""

        parsed_tree = self._parse_source(tex_source)
        self.context["parser_engine_used"] = "plastex"
        self._render_stack.clear()
        self.handle_event("load", tex_source, parsed_tree)
        self._walk(self._root_nodes(parsed_tree))
        self._flush_paragraph()
        self.handle_event("post_process")

    def _parse_source(self, tex_source):
        from plasTeX.TeX import TeX

        parse_source = self._sanitize_source_for_parse(tex_source)
        parsed = None
        parse_error = None
        try:
            tex = TeX()
            for macro_name, macro_class in self.macro_handlers.items():
                tex.ownerDocument.context.addGlobal(macro_name, macro_class)
            tex.input(parse_source)
            parsed = tex.parse()
        except Exception as exc:
            parse_error = exc

        if parsed is None:
            if "\\begin{document}" in parse_source:
                body = self._extract_document_body(parse_source)
                if body is not None:
                    fallback_tex = TeX()
                    for macro_name, macro_class in self.macro_handlers.items():
                        fallback_tex.ownerDocument.context.addGlobal(
                            macro_name, macro_class
                        )
                    fallback_tex.input(body)
                    self.context.setdefault("warnings", []).append(
                        f"Full LaTeX parse failed ({type(parse_error).__name__}); used body-only parse fallback."
                    )
                    return fallback_tex.parse()
            raise parse_error

        if self._looks_like_preamble_only(parsed) and "\\begin{document}" in parse_source:
            body = self._extract_document_body(parse_source)
            if body is not None:
                fallback_tex = TeX()
                for macro_name, macro_class in self.macro_handlers.items():
                    fallback_tex.ownerDocument.context.addGlobal(macro_name, macro_class)
                fallback_tex.input(body)
                self.context.setdefault("warnings", []).append(
                    "Full LaTeX parse produced no document body; used body-only parse fallback."
                )
                return fallback_tex.parse()
        return parsed

    def _sanitize_source_for_parse(self, tex_source: str) -> str:
        skip_packages = set(
            p.strip()
            for p in (self.context.get("parse_skip_packages") or [])
            if str(p).strip()
        )
        skip_paths = set(
            p.strip()
            for p in (self.context.get("parse_skip_usepackage_paths") or [])
            if str(p).strip()
        )
        if not skip_packages and not skip_paths:
            return tex_source

        usepackage_re = re.compile(
            r"\\usepackage(?P<opts>\s*\[[^\]]*\])?\s*\{(?P<pkgs>[^}]*)\}"
        )
        warnings = self.context.setdefault("warnings", [])

        def _replace(match: re.Match) -> str:
            opts = match.group("opts") or ""
            pkgs_raw = match.group("pkgs")
            packages = [pkg.strip() for pkg in pkgs_raw.split(",") if pkg.strip()]
            if not packages:
                return match.group(0)

            kept: list[str] = []
            removed: list[str] = []
            for pkg in packages:
                if pkg in skip_packages or pkg in skip_paths:
                    removed.append(pkg)
                else:
                    kept.append(pkg)
            if not removed:
                return match.group(0)

            warnings.append(
                f"Skipped usepackage for parser compatibility: {', '.join(removed)}"
            )
            if not kept:
                return ""
            return f"\\usepackage{opts}" + "{" + ",".join(kept) + "}"

        return usepackage_re.sub(_replace, tex_source)

    def _looks_like_preamble_only(self, parsed_tree):
        meaningful = False
        for node in self._root_nodes(parsed_tree):
            if self._node_kind(node) == "text":
                if str(node).strip():
                    meaningful = True
                    break
                continue
            name = self._node_name(node)
            if not name or name in {"documentclass", "usepackage", "par", "#text"}:
                continue
            meaningful = True
            break
        return not meaningful

    def _extract_document_body(self, tex_source):
        match = re.search(
            r"\\begin\{document\}(.*?)\\end\{document\}",
            tex_source,
            flags=re.S,
        )
        if not match:
            return None
        return match.group(1)

    def _root_nodes(self, parsed_tree):
        body = getattr(parsed_tree, "document", None) or parsed_tree
        if hasattr(body, "contents"):
            return body.contents
        if hasattr(body, "childNodes"):
            return body.childNodes
        return []

    def _node_name(self, node):
        node_name = getattr(node, "nodeName", None)
        return str(node_name).lstrip("\\") if node_name else ""

    def _node_children(self, node):
        return list(getattr(node, "childNodes", []) or [])

    def _node_kind(self, node):
        if isinstance(node, Text) or isinstance(node, str):
            return "text"
        if isinstance(node, Environment):
            return "environment"
        if isinstance(node, Command):
            return "command"
        return "other"

    def _walk(self, nodes, style=None):
        active_style = dict(style) if style else {}
        for node in nodes:
            kind = self._node_kind(node)

            if kind == "text":
                self._append_node_text(node, active_style)
                continue

            name = self._node_name(node)
            special_text = self._special_text_for_node(name)
            if special_text is not None:
                self._append_text(special_text, active_style)
                continue
            if name in {"#document", "document"}:
                self._walk(self._node_children(node), active_style)
                continue
            if name == "par":
                paragraph = self._active_paragraph()
                preserve_flag = bool(self.context.get("_preserve_paragraph_once"))
                preserve_current = preserve_flag or (
                    paragraph is not None and len(paragraph.runs) == 0
                )
                if preserve_flag:
                    self.context["_preserve_paragraph_once"] = False
                if not preserve_current:
                    self._flush_paragraph()
                self._walk(self._node_children(node), active_style)
                self._flush_paragraph()
                continue

            children = self._node_children(node)
            declaration_style = self._declaration_styles.get(name)
            if declaration_style is not None:
                active_style = {**active_style, **declaration_style}
                if children:
                    self._walk(children, active_style)
                continue
            if name in self._inline_styles:
                self._walk(children, {**active_style, **self._inline_styles[name]})
                continue

            handler_entry = self.command_handlers.get(name)
            if handler_entry:
                handler, inline_mode = handler_entry
                if not inline_mode:
                    self._flush_paragraph()
                handler(node)
                if not inline_mode:
                    self._walk(children, active_style)
                    self._flush_paragraph()
                continue

            env_handler = self.env_handlers.get(name)
            if env_handler:
                self._flush_paragraph()
                env_handler(node)
                self._flush_paragraph()
                continue

            self._walk(children, active_style)

    def render_nodes(self, nodes, style=None):
        self._walk(list(nodes or []), style=style)

    def render_latex_fragment(self, tex_source: str, *, paragraph=None, style=None):
        """
        Parse and render a LaTeX fragment through the regular node walker.
        This reuses existing command/env handlers and inline style handling.
        """
        from plasTeX.TeX import TeX

        tex = TeX()
        for macro_name, macro_class in self.macro_handlers.items():
            tex.ownerDocument.context.addGlobal(macro_name, macro_class)
        tex.input(tex_source)
        parsed = tex.parse()
        nodes = self._root_nodes(parsed)
        with self.render_frame(paragraph=paragraph):
            self._walk(nodes, style=style)

    @contextmanager
    def render_frame(self, *, paragraph=None, link=None):
        frame = {}
        if paragraph is not None:
            frame["paragraph"] = paragraph
        if link is not None:
            frame["link"] = link
        self._render_stack.append(frame)
        try:
            yield
        finally:
            self._render_stack.pop()

    def _active_frame_value(self, key):
        for frame in reversed(self._render_stack):
            if key in frame:
                return frame[key]
        return None

    def _special_text_for_node(self, node_name: str):
        # LaTeX tie (`~`) should render as a non-breaking space.
        if node_name == "active::~":
            return "\u00A0"
        literal_map = {
            "%": "%",
            "_": "_",
            "#": "#",
            "&": "&",
            "{": "{",
            "}": "}",
        }
        if node_name in literal_map:
            return literal_map[node_name]
        return None

    def save(self, filename):
        self.doc.save(filename)

    def get_arg_text(self, node, index, default="", key=None):
        args = getattr(node, "args", None)
        if args and not isinstance(args, str) and len(args) > index:
            value = str(args[index]).strip()
            return value.strip("{}")

        attributes = getattr(node, "attributes", None)
        if attributes:
            if key in attributes and attributes[key] is not None:
                return self._stringify_attr_value(attributes[key])
            values = [
                v
                for k, v in attributes.items()
                if v is not None and k not in {"*modifier*", "toc", "len"}
            ]
            if len(values) > index:
                return self._stringify_attr_value(values[index])
        return default

    def _stringify_attr_value(self, value):
        if isinstance(value, list):
            return ",".join(str(item).strip() for item in value if str(item).strip())
        source = getattr(value, "source", None)
        if source is not None:
            return str(source).strip("{} ")
        text_content = getattr(value, "textContent", None)
        if text_content is not None:
            return str(text_content).strip("{} ")
        child_nodes = getattr(value, "childNodes", None)
        if child_nodes:
            text = "".join(str(node) for node in child_nodes if node is not None)
            if text.strip():
                return text.strip("{} ")
        return str(value).strip("{} ")

    def get_node_name(self, node):
        node_name = getattr(node, "nodeName", None)
        if node_name is None:
            return None
        return str(node_name).lstrip("\\")

    def get_node_text(self, node):
        string_attr = getattr(node, "string", None)
        if string_attr is not None:
            text = str(string_attr).strip()
            if text:
                return text

        contents = getattr(node, "contents", None)
        if contents:
            return "".join(str(child) for child in contents if child is not None)

        children = getattr(node, "childNodes", None)
        if children:
            return "".join(str(child) for child in children if child is not None)

        attributes = getattr(node, "attributes", None)
        if attributes:
            text_parts = []
            for value in attributes.values():
                if value is None:
                    continue
                part = self._stringify_attr_value(value)
                if part:
                    text_parts.append(part)
            if text_parts:
                return " ".join(text_parts)

        return str(node)

    def get_math_source(self, node):
        source = getattr(node, "source", None)
        if source:
            source = str(source).strip()
            if source.startswith("\\begin{equation}") and source.endswith(
                "\\end{equation}"
            ):
                source = source[
                    len("\\begin{equation}") : -len("\\end{equation}")
                ].strip()
                return source
            if source.startswith("\\(") and source.endswith("\\)"):
                return source[2:-2].strip()
            if source.startswith("$") and source.endswith("$") and len(source) >= 2:
                return source[1:-1].strip()
            return source

        return self.get_node_text(node)

    def _append_node_text(self, node, style):
        text = str(node).replace("\n", " ")
        if self.context.get("_trim_next_leading_space_once"):
            text = text.lstrip(" ")
            self.context["_trim_next_leading_space_once"] = False
        if text == "":
            return
        paragraph = self._active_paragraph()
        if text.isspace():
            if paragraph is None:
                return
            if not paragraph.runs:
                return
            if paragraph.runs[-1].text.endswith(" "):
                return
            text = " "
        self._append_text(text, style)

    def _ensure_paragraph(self):
        if self._active_frame_value("paragraph") is not None:
            return
        if self._current_paragraph is None:
            role = self._next_body_role
            style_name = self._resolve_paragraph_style(role)
            if style_name:
                self._current_paragraph = self.doc.add_paragraph(style=style_name)
            else:
                self._current_paragraph = self.doc.add_paragraph()
            self._next_body_role = "body"

    def _resolve_paragraph_style(self, role):
        candidates = self.style_table.get(role, [])
        if isinstance(candidates, str):
            candidates = [candidates]
        paragraph_styles = [style for style in self.doc.styles if style.type == 1]
        styles_by_name = {style.name: style for style in paragraph_styles}
        style_name_by_id = {style.style_id: style.name for style in paragraph_styles}

        for candidate in candidates:
            if candidate in styles_by_name:
                return candidate
            resolved_name = style_name_by_id.get(candidate)
            if resolved_name:
                return resolved_name
        return None

    def mark_next_body_paragraph_first(self):
        self._next_body_role = "first_body"

    def add_paragraph_for_role(self, role):
        style_name = self._resolve_paragraph_style(role)
        if style_name:
            return self.doc.add_paragraph(style=style_name)
        return self.doc.add_paragraph()

    def _append_text(self, text, style):
        self._ensure_paragraph()
        paragraph = self._active_paragraph()
        if paragraph is None:
            return
        link = self._active_frame_value("link")
        if link is not None:
            self._append_hyperlink_run(paragraph, text, link, style or {})
            return
        run = paragraph.add_run(text)
        apply_theme_font(run, style.get("theme", "minor"))
        if style.get("monospace"):
            run.font.name = "Courier New"
        if style.get("bold"):
            run.bold = True
        if style.get("italic"):
            run.italic = True
        if style.get("small_caps"):
            run.font.small_caps = True

    def _active_paragraph(self):
        return self._active_frame_value("paragraph") or self._current_paragraph

    def _append_hyperlink_run(self, paragraph, text, link, style):
        hyperlink = OxmlElement("w:hyperlink")
        if link.get("anchor"):
            hyperlink.set(qn("w:anchor"), link["anchor"])
        elif link.get("url"):
            rel_id = link.get("rel_id")
            if rel_id is None:
                rel_id = paragraph.part.relate_to(
                    link["url"], RT.HYPERLINK, is_external=True
                )
                link["rel_id"] = rel_id
            hyperlink.set(qn("r:id"), rel_id)
        else:
            run = paragraph.add_run(text)
            apply_theme_font(run, style.get("theme", "minor"))
            return

        run = OxmlElement("w:r")
        r_pr = OxmlElement("w:rPr")
        r_style = OxmlElement("w:rStyle")
        r_style.set(qn("w:val"), "Hyperlink")
        r_pr.append(r_style)
        if style.get("bold"):
            r_pr.append(OxmlElement("w:b"))
        if style.get("italic"):
            r_pr.append(OxmlElement("w:i"))
        if style.get("small_caps"):
            r_pr.append(OxmlElement("w:smallCaps"))
        r_fonts = OxmlElement("w:rFonts")
        if style.get("monospace"):
            r_fonts.set(qn("w:ascii"), "Courier New")
            r_fonts.set(qn("w:hAnsi"), "Courier New")
            r_fonts.set(qn("w:cs"), "Courier New")
        else:
            theme = style.get("theme", "minor")
            val = "major" if theme == "major" else "minor"
            r_fonts.set(qn("w:asciiTheme"), f"{val}Ascii")
            r_fonts.set(qn("w:hAnsiTheme"), f"{val}HAnsi")
        r_pr.append(r_fonts)
        run.append(r_pr)
        text_node = OxmlElement("w:t")
        text_node.text = text
        run.append(text_node)
        hyperlink.append(run)
        paragraph._p.append(hyperlink)

    def _flush_paragraph(self):
        self._current_paragraph = None

    def append_inline(self, text, style=None):
        self._append_text(text, style or {})

    def append_math(self, latex_str):
        self._ensure_paragraph()
        paragraph = self._active_paragraph()
        if paragraph is None:
            return
        if self._active_frame_value("link") is not None:
            # DOCX hyperlinks don't safely embed OMML; keep math text visible.
            self._append_text(latex_str, {"theme": "minor"})
            return
        xsl_path = self.context.get("mathml2omml_xsl_path")
        ok = inject_omml(paragraph, latex_str, xsl_path=xsl_path)
        if not ok and not xsl_path:
            msg = (
                "Math OMML stylesheet path is not configured "
                "(set mathml2omml_xsl_path in config)."
            )
            warnings = self.context.setdefault("warnings", [])
            if msg not in warnings:
                warnings.append(msg)
