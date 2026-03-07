from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
import re

from jinja2 import Environment
from plasTeX import Command
from plasTeX.TeX import TeX


class entry(Command):
    args = "key type options"


class endentry(Command):
    args = ""


class field(Command):
    args = "key value"


class list_(Command):
    macroName = "list"
    args = "key count value"


class name(Command):
    args = "role count opts payload"


class strng(Command):
    args = "key value"


class range_(Command):
    macroName = "range"
    args = "key value"


class verb(Command):
    args = "key"


class endverb(Command):
    args = ""


class bibitem(Command):
    args = "[label] key:str"


class BibitemOpen(Command):
    args = ""


class BibitemShut(Command):
    args = "kind:str"


class bibfield(Command):
    args = "kind value"


class bibinfo(Command):
    args = "kind value"


class bibitemNoStop(Command):
    args = ""


class bibitemStop(Command):
    args = ""


class EOS(Command):
    args = ""


class bibfnamefont(Command):
    args = "self"


class bibnamefont(Command):
    args = "self"


class citenamefont(Command):
    args = "self"


class href(Command):
    args = "url:str self"


@dataclass
class BblEntry:
    key: str
    entry_type: str
    raw_fields: dict[str, str] = dataclass_field(default_factory=dict)
    raw_lists: dict[str, list[str]] = dataclass_field(default_factory=dict)
    raw_authors: list[str] = dataclass_field(default_factory=list)
    raw_author_names: list[dict[str, str]] = dataclass_field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "type": self.entry_type,
            "fields": {k: _preserve_tex_text(v) for k, v in self.raw_fields.items()},
            "lists": {
                k: [_preserve_tex_text(v) for v in values]
                for k, values in self.raw_lists.items()
            },
            "authors": [_preserve_tex_text(a) for a in self.raw_authors],
            "author_names": [
                {k: str(v).strip() for k, v in author.items()}
                for author in self.raw_author_names
            ],
        }


@dataclass
class _VerbCapture:
    field_key: str | None = None
    collecting_value: bool = False
    parts: list[str] = dataclass_field(default_factory=list)

    def start_key(self, key: str):
        self.field_key = key
        self.collecting_value = False
        self.parts = []

    def start_value(self, first_fragment: str):
        self.collecting_value = True
        self.parts = [first_fragment] if first_fragment else []

    def append_text(self, text: str):
        if self.collecting_value:
            self.parts.append(text)

    def finish(self) -> tuple[str | None, str]:
        key = self.field_key
        value = "".join(self.parts)
        self.field_key = None
        self.collecting_value = False
        self.parts = []
        return key, value


def _is_escaped(text: str, idx: int) -> bool:
    backslashes = 0
    j = idx - 1
    while j >= 0 and text[j] == "\\":
        backslashes += 1
        j -= 1
    return (backslashes % 2) == 1


def _skip_ws(text: str, i: int) -> int:
    while i < len(text) and text[i].isspace():
        i += 1
    return i


def _read_braced(text: str, i: int) -> tuple[str, int]:
    i = _skip_ws(text, i)
    if i >= len(text) or text[i] != "{":
        return "", i
    depth = 0
    i += 1
    start = i
    while i < len(text):
        ch = text[i]
        if ch == "{" and not _is_escaped(text, i):
            depth += 1
        elif ch == "}" and not _is_escaped(text, i):
            if depth == 0:
                return text[start:i], i + 1
            depth -= 1
        i += 1
    return text[start:], len(text)


def _normalize_identifier(value: str) -> str:
    return str(value).strip().strip("{}")


def _preserve_tex_text(value: str) -> str:
    # Keep TeX tokens intact so bibliography rendering can flow through the
    # regular parser/emitter pipeline without broad lossy normalization.
    # Normalize only spacing/control macros that should not remain symbolic.
    text = str(value).strip()
    replacements = {
        "\\bibinitperiod": ".",
        "\\bibnamedelima": " ",
        "\\bibinitdelim": " ",
        "\\bibinithyphendelim": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _fragment_raw_text(value) -> str:
    if value is None:
        return ""
    source = getattr(value, "source", None)
    if source is not None:
        return str(source)
    text_content = getattr(value, "textContent", None)
    if text_content is not None:
        return str(text_content)
    return str(value)


def _extract_all_named_group_values(payload: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    pattern = re.compile(r"([A-Za-z][A-Za-z0-9_]*)=\{")
    i = 0
    while i < len(payload):
        match = pattern.search(payload, i)
        if match is None:
            break
        key = match.group(1)
        start = match.end() - 1
        value, nxt = _read_braced(payload, start)
        values.setdefault(key, []).append(value)
        i = max(i + 1, nxt)
    return values


def _create_tex_with_bbl_macros() -> TeX:
    tex = TeX()
    context = tex.ownerDocument.context
    for macro_name, macro_class in {
        "bibitem": bibitem,
        "BibitemOpen": BibitemOpen,
        "BibitemShut": BibitemShut,
        "bibfield": bibfield,
        "bibinfo": bibinfo,
        "bibitemNoStop": bibitemNoStop,
        "bibitemStop": bibitemStop,
        "EOS": EOS,
        "bibfnamefont": bibfnamefont,
        "bibnamefont": bibnamefont,
        "citenamefont": citenamefont,
        "href": href,
        "entry": entry,
        "endentry": endentry,
        "field": field,
        "list": list_,
        "name": name,
        "strng": strng,
        "range": range_,
        "verb": verb,
        "endverb": endverb,
    }.items():
        context.addGlobal(macro_name, macro_class)
    return tex


def _tex_to_plaintext(source: str) -> str:
    one_arg_wrappers = {
        "textbf",
        "textit",
        "emph",
        "url",
        "bibfnamefont",
        "bibnamefont",
        "citenamefont",
        "natexlab",
    }
    two_arg_keep_second = {"bibfield", "bibinfo", "href", "Eprint"}
    spacing_macros = {
        ",": ",",
        " ": " ",
        "quad": " ",
        "qquad": " ",
        "slash": "/",
    }

    def _walk(text: str) -> str:
        out: list[str] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "%":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            if ch == "{":
                i += 1
                continue
            if ch == "}":
                i += 1
                continue
            if ch != "\\":
                out.append(ch)
                i += 1
                continue

            i += 1
            if i >= len(text):
                break
            token = text[i]
            if token.isalpha() or token == "@":
                j = i
                while j < len(text) and (text[j].isalpha() or text[j] == "@"):
                    j += 1
                cmd = text[i:j]
                i = j
            else:
                cmd = token
                i += 1

            if cmd in spacing_macros:
                out.append(spacing_macros[cmd])
                continue
            if cmd in {"BibitemOpen", "BibitemShut", "bibitemStop", "bibitemNoStop"}:
                if cmd == "BibitemShut":
                    _ignored, i = _read_braced(text, i)
                continue
            if cmd in two_arg_keep_second:
                _ignored, i = _read_braced(text, i)
                value, i2 = _read_braced(text, i)
                if i2 != i:
                    out.append(_walk(value))
                    i = i2
                continue
            if cmd in one_arg_wrappers:
                value, i2 = _read_braced(text, i)
                if i2 != i:
                    out.append(_walk(value))
                    i = i2
                continue

            value, i2 = _read_braced(text, i)
            if i2 != i:
                out.append(_walk(value))
                i = i2
            # Unknown control sequence without braces: drop token.

        text_out = "".join(out)
        text_out = re.sub(r"\s+", " ", text_out).strip()
        text_out = re.sub(r"\s+([,.;:])", r"\1", text_out)
        text_out = text_out.replace(" .", ".")
        text_out = text_out.replace("$", "")
        text_out = text_out.replace("~", " ")
        return text_out

    return _walk(source)


def _slice_revtex_bibliography(source: str) -> str:
    start = source.find("\\bibitem")
    if start == -1:
        return source
    end = source.rfind("\\end{thebibliography}")
    if end != -1 and end > start:
        return source[start:end]
    return source[start:]


def _collect_revtex_entries(doc) -> dict[str, dict]:
    entries: dict[str, dict] = {}

    current_key: str | None = None
    current_chunks: list[str] = []

    def _flush_current():
        nonlocal current_key, current_chunks
        if not current_key:
            return
        plain_text = _tex_to_plaintext(" ".join(current_chunks))
        entries[current_key] = {
            "key": current_key,
            "type": "revtex-bibitem",
            "fields": {},
            "authors": [],
            "author_names": [],
            "plain_text": plain_text,
        }

    for node in getattr(doc, "childNodes", []):
        node_name = getattr(node, "nodeName", None)
        if node_name == "bibitem":
            _flush_current()
            current_chunks = []
            key = _normalize_identifier(_fragment_raw_text(node.attributes.get("key")))
            current_key = key or None
            continue
        if current_key is None:
            continue
        if node_name == "bibfield":
            current_chunks.append(_fragment_raw_text(node.attributes.get("value")))
            continue
        if node_name in {"href", "Eprint"}:
            current_chunks.append(_fragment_raw_text(node.attributes.get("self")))
            continue
        if node_name == "#text":
            current_chunks.append(str(node))
            continue

    _flush_current()
    return entries


def _collect_entries(doc) -> dict[str, BblEntry]:
    entries: dict[str, BblEntry] = {}
    current: BblEntry | None = None
    verb_capture = _VerbCapture()

    for node in getattr(doc, "childNodes", []):
        node_name = getattr(node, "nodeName", None)

        if node_name == "entry":
            key = _normalize_identifier(_fragment_raw_text(node.attributes.get("key")))
            entry_type = _normalize_identifier(
                _fragment_raw_text(node.attributes.get("type"))
            )
            current = BblEntry(key=key, entry_type=entry_type)
            verb_capture = _VerbCapture()
            continue

        if current is None:
            continue

        if verb_capture.collecting_value:
            if node_name == "endverb":
                key, value = verb_capture.finish()
                if key:
                    current.raw_fields[key] = value
                continue
            if node_name == "#text":
                verb_capture.append_text(str(node))
            continue

        if node_name == "field":
            key = _normalize_identifier(_fragment_raw_text(node.attributes.get("key")))
            value = _fragment_raw_text(node.attributes.get("value"))
            if key:
                current.raw_fields[key] = value
            continue

        if node_name == "list":
            key = _normalize_identifier(_fragment_raw_text(node.attributes.get("key")))
            value = _fragment_raw_text(node.attributes.get("value"))
            if key:
                current.raw_lists.setdefault(key, []).append(value)
            continue

        if node_name == "name":
            role = _normalize_identifier(_fragment_raw_text(node.attributes.get("role")))
            payload = node.attributes.get("payload")
            payload_source = str(getattr(payload, "source", "") or "")
            if role == "author":
                all_fields = _extract_all_named_group_values(payload_source)
                author_count = max((len(vals) for vals in all_fields.values()), default=0)
                families = all_fields.get("family", [])
                givens = all_fields.get("given", [])
                for idx in range(author_count):
                    author_parts: dict[str, str] = {}
                    for key, vals in all_fields.items():
                        if idx < len(vals):
                            author_parts[key] = vals[idx]
                    if author_parts:
                        current.raw_author_names.append(author_parts)
                    family = families[idx] if idx < len(families) else ""
                    given = givens[idx] if idx < len(givens) else ""
                    author = f"{family}, {given}".strip().strip(",")
                    if author:
                        current.raw_authors.append(author)
            continue

        if node_name == "verb":
            source_text = str(getattr(node, "source", "") or "")
            key = _normalize_identifier(_fragment_raw_text(node.attributes.get("key")))
            if source_text.startswith("\\verb{") and key:
                verb_capture.start_key(key)
            elif verb_capture.field_key:
                verb_capture.start_value(key)
            continue

        if node_name == "endentry":
            if verb_capture.collecting_value and verb_capture.field_key:
                key, value = verb_capture.finish()
                if key:
                    current.raw_fields[key] = value
            entries[current.key] = current
            current = None
            verb_capture = _VerbCapture()

    return entries


def parse_bbl(fname: str | Path) -> dict[str, dict]:
    source = Path(fname).read_text(encoding="utf-8")
    start = source.find("\\refsection")
    if start != -1:
        source = source[start:]

    tex = _create_tex_with_bbl_macros()
    tex.input(source)
    doc = tex.parse()

    entries = _collect_entries(doc)
    if entries:
        return {key: entry_data.to_dict() for key, entry_data in entries.items()}

    # RevTeX/apsrev-style .bbl files use \bibitem blocks instead of biblatex
    # \entry structures. Parse those blocks through plasTeX and extract plain
    # reference rows from parsed nodes.
    revtex_source = _slice_revtex_bibliography(Path(fname).read_text(encoding="utf-8"))
    revtex_tex = _create_tex_with_bbl_macros()
    revtex_tex.input(revtex_source)
    revtex_doc = revtex_tex.parse()
    return _collect_revtex_entries(revtex_doc)


DEFAULT_BIB_TEMPLATE = r"""
<%- if authors -%>
<%- if authors|length > et_al_limit -%>
<<- authors[:et_al_limit]|join(", ") ->>, \textit{et al.}
<%- else -%>
<<- authors|join(", ") ->>
<%- endif -%>.
<%- endif -%>
<%- if fields.year -%> (<<- fields.year ->>).<%- endif -%>
<%- if fields.title -%> <<- fields.title ->>.<%- endif -%>
<%- if fields.journaltitle or fields.volume or fields.number or fields.pages -%>
 <%- if fields.journaltitle -%>\textit{<<- fields.journaltitle ->>}<%- endif -%><%- if fields.volume and fields.number -%>, <<- fields.volume ->>(<<- fields.number ->>)<%- elif fields.volume -%>, <<- fields.volume ->><%- endif -%><%- if fields.pages -%>, <<- fields.pages ->><%- endif -%>.
<%- endif -%>
<%- if fields.doi -%> DOI: \href{https://doi.org/<<- fields.doi ->>}{<<- fields.doi ->>}.<%- endif -%>
""".strip()


def _bibliography_template_env() -> Environment:
    return Environment(
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
    )


def _cleanup_bibliography_latex(text: str) -> str:
    # Keep bibliography output stable with upstream biber/biblatex formatting.
    # Only trim outer whitespace introduced by template block layout.
    return text.strip()


def format_bibliography_entry(
    entry_data: dict,
    template: str | None = None,
    et_al_limit: int = 3,
) -> str:
    plain_text = str(entry_data.get("plain_text", "")).strip()
    if plain_text:
        return plain_text
    fields = entry_data.get("fields", {})
    authors = [a for a in entry_data.get("authors", []) if a]
    author_names = [
        a for a in entry_data.get("author_names", []) if isinstance(a, dict) and a
    ]
    env = _bibliography_template_env()
    compiled = env.from_string(template or DEFAULT_BIB_TEMPLATE)
    if et_al_limit <= 0:
        et_al_limit = 3
    rendered = compiled.render(
        authors=authors,
        author_names=author_names,
        fields=fields,
        et_al_limit=et_al_limit,
    )
    return _cleanup_bibliography_latex(rendered)
