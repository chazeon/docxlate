from __future__ import annotations

from plasTeX import Command, Environment

from docxlate.registry import MacroSpec


class table(Environment):
    args = "[ position ]"


class tabular(Environment):
    args = "colspec:str"


class multicolumn(Command):
    args = "cols:str align:str self"


def table_specs() -> list[MacroSpec]:
    return [
        MacroSpec(
            name="table",
            kind="env",
            parse_class=table,
            policy="stub",
        ),
        MacroSpec(
            name="tabular",
            kind="env",
            parse_class=tabular,
            policy="stub",
        ),
        MacroSpec(
            name="multicolumn",
            kind="command",
            parse_class=multicolumn,
            policy="stub",
        ),
    ]


def register(latex):
    latex.register_specs(table_specs())
    return None


__all__ = ["register", "table_specs"]
