from __future__ import annotations

import re

from plasTeX import Command

from docxlate.registry import MacroSpec

_USEPACKAGE_RE = re.compile(
    r"\\usepackage(?:\s*\[[^\]]*\])?\s*\{(?P<pkgs>[^}]*)\}"
)
_COLOR_DECL_RE = re.compile(r"\\color(?:\s*\[[^\]]*\])?\s*\{")


class color(Command):
    args = "color:str"


class textcolor(Command):
    args = "color:str self"


def _source_uses_package(tex_source: str, package_name: str) -> bool:
    for match in _USEPACKAGE_RE.finditer(tex_source):
        raw = match.group("pkgs")
        pkgs = [pkg.strip() for pkg in raw.split(",") if pkg.strip()]
        if package_name in pkgs:
            return True
    return False


def _source_uses_color_declaration(tex_source: str) -> bool:
    return bool(_COLOR_DECL_RE.search(tex_source))


def register(latex):
    def _initial_xcolor_skip_policy(
        tex_source: str,
        configured_skip_packages: set[str],
        _parse_error: Exception | None = None,
    ) -> set[str]:
        if "xcolor" in configured_skip_packages:
            return set()
        if _source_uses_package(tex_source, "xcolor") and _source_uses_color_declaration(
            tex_source
        ):
            return {"xcolor"}
        return set()

    def _retry_xcolor_skip_policy(
        tex_source: str,
        configured_skip_packages: set[str],
        _parse_error: Exception | None = None,
    ) -> set[str]:
        if "xcolor" in configured_skip_packages:
            return set()
        if _source_uses_package(tex_source, "xcolor"):
            return {"xcolor"}
        return set()

    latex.register_parse_skip_policy(
        initial=_initial_xcolor_skip_policy,
        retry=_retry_xcolor_skip_policy,
    )

    latex.register_spec(
        MacroSpec(
            name="color",
            kind="command",
            parse_class=color,
            policy="declaration",
        )
    )

    @latex.command("textcolor", inline=True, parse_class=textcolor)
    def handle_textcolor(node):
        value = latex.get_arg_text(node, 0, key="color")
        text_fragment = getattr(node, "attributes", {}).get("self")
        style = {"color": value} if value else None
        if text_fragment is not None and getattr(text_fragment, "childNodes", None):
            latex.render_nodes(text_fragment.childNodes, style=style)
            return
        text = latex.get_arg_text(node, 1, key="self")
        if text:
            latex.append_inline(text, style=style)

    return None


__all__ = ["register"]
