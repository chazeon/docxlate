from __future__ import annotations

from plasTeX import Command

from docxlate.registry import MacroSpec


class color(Command):
    args = "color:str"


class textcolor(Command):
    args = "color:str self"


def register(latex):
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
