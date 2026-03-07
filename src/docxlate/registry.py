from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from plasTeX import Command, Environment

MacroKind = Literal["command", "env"]
MacroPolicy = Literal["render", "stub", "declaration"]


@dataclass(frozen=True, slots=True)
class MacroSpec:
    name: str
    kind: MacroKind
    parse_class: type[Command] | type[Environment] | None = None
    handler: Callable | None = None
    inline: bool = False
    policy: MacroPolicy = "render"


def normalize_macro_name(name: str) -> str:
    return str(name or "").strip().lstrip("\\")


def validate_macro_spec(spec: MacroSpec) -> None:
    name = normalize_macro_name(spec.name)
    if not name:
        raise ValueError("MacroSpec.name must be non-empty")

    if spec.kind not in {"command", "env"}:
        raise ValueError(f"MacroSpec({name}) has invalid kind: {spec.kind!r}")

    if spec.policy not in {"render", "stub", "declaration"}:
        raise ValueError(f"MacroSpec({name}) has invalid policy: {spec.policy!r}")

    if spec.inline and spec.kind != "command":
        raise ValueError(f"MacroSpec({name}) sets inline=True but kind is {spec.kind!r}")

    if spec.parse_class is not None:
        if not isinstance(spec.parse_class, type):
            raise ValueError(f"MacroSpec({name}) parse_class must be a class type")
        if spec.kind == "command" and not issubclass(
            spec.parse_class, (Command, Environment)
        ):
            raise ValueError(
                f"MacroSpec({name}) kind='command' requires parse_class subclassing "
                "plasTeX.Command or plasTeX.Environment"
            )
        if spec.kind == "env" and not issubclass(spec.parse_class, Environment):
            raise ValueError(
                f"MacroSpec({name}) kind='env' requires parse_class subclassing plasTeX.Environment"
            )

    if spec.policy == "render":
        if spec.parse_class is None or spec.handler is None:
            raise ValueError(
                f"MacroSpec({name}) policy='render' requires both parse_class and handler"
            )
        return

    if spec.policy == "stub":
        if spec.parse_class is None:
            raise ValueError(
                f"MacroSpec({name}) policy='stub' requires a parse_class for parse-time support"
            )
        if spec.handler is not None:
            raise ValueError(
                f"MacroSpec({name}) policy='stub' must not define a runtime handler"
            )
        return

    # declaration policy
    if spec.parse_class is None:
        raise ValueError(
            f"MacroSpec({name}) policy='declaration' requires a parse_class"
        )
    if spec.handler is not None:
        raise ValueError(
            f"MacroSpec({name}) policy='declaration' must not define a runtime handler"
        )


__all__ = [
    "MacroKind",
    "MacroPolicy",
    "MacroSpec",
    "normalize_macro_name",
    "validate_macro_spec",
]
