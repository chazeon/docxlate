from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .emit import StyleState, TextSpan


@dataclass(frozen=True)
class RenderContext:
    style: StyleState = StyleState()
    char_role: str | None = None
    para_role: str | None = None

    @classmethod
    def from_style_mapping(
        cls, style: Mapping[str, object] | None, *, fallback: "RenderContext | None" = None
    ) -> "RenderContext":
        ctx = fallback or cls()
        if not style:
            return ctx
        return ctx.apply_style_delta(style).with_char_role(
            _as_optional_str(style.get("char_role"))
        )

    def apply_style_delta(self, delta: Mapping[str, object] | None) -> "RenderContext":
        if not delta:
            return self
        style = self.style
        theme = style.theme
        if "theme" in delta and delta.get("theme") is not None:
            theme = str(delta.get("theme"))
        return RenderContext(
            style=StyleState(
                theme=theme,
                bold=_pick_bool(delta, "bold", style.bold),
                italic=_pick_bool(delta, "italic", style.italic),
                small_caps=_pick_bool(delta, "small_caps", style.small_caps),
                monospace=_pick_bool(delta, "monospace", style.monospace),
            ),
            char_role=self.char_role,
            para_role=self.para_role,
        )

    def with_char_role(self, char_role: str | None) -> "RenderContext":
        if char_role is None:
            return self
        return RenderContext(style=self.style, char_role=char_role, para_role=self.para_role)

    def with_para_role(self, para_role: str | None) -> "RenderContext":
        if para_role is None:
            return self
        return RenderContext(style=self.style, char_role=self.char_role, para_role=para_role)


class SpanCompositor:
    def compose(
        self,
        text: str,
        *,
        base: RenderContext,
        style_delta: Mapping[str, object] | None = None,
        role: str | None = None,
    ) -> TextSpan:
        ctx = base.apply_style_delta(style_delta).with_char_role(role)
        return TextSpan(text=text, style=ctx.style, char_role=ctx.char_role)


def _pick_bool(delta: Mapping[str, object], key: str, fallback: bool) -> bool:
    if key not in delta or delta.get(key) is None:
        return fallback
    return bool(delta.get(key))


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
