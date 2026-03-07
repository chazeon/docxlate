from __future__ import annotations

import pytest
from plasTeX import Command, Environment

from docxlate.core import LatexBridge
from docxlate.handlers import latex
from docxlate.registry import MacroSpec


class DemoCommand(Command):
    args = "self"


class DemoEnv(Environment):
    args = "self"


def _noop(_node):
    return None


def test_render_spec_requires_parse_class_and_handler():
    bridge = LatexBridge()

    with pytest.raises(ValueError, match="policy='render' requires both parse_class and handler"):
        bridge.register_spec(
            MacroSpec(
                name="demo",
                kind="command",
                parse_class=DemoCommand,
                policy="render",
            )
        )

    with pytest.raises(ValueError, match="policy='render' requires both parse_class and handler"):
        bridge.register_spec(
            MacroSpec(
                name="demo2",
                kind="command",
                handler=_noop,
                policy="render",
            )
        )


def test_parse_only_spec_must_use_explicit_stub_policy():
    bridge = LatexBridge()

    with pytest.raises(ValueError, match="policy='render' requires both parse_class and handler"):
        bridge.register_spec(
            MacroSpec(
                name="parseonly",
                kind="command",
                parse_class=DemoCommand,
            )
        )


def test_command_spec_can_use_environment_parse_class_for_math_like_nodes():
    bridge = LatexBridge()
    bridge.register_spec(
        MacroSpec(
            name="mathlike",
            kind="command",
            parse_class=DemoEnv,
            handler=_noop,
            policy="render",
        )
    )
    assert bridge.macro_specs["mathlike"].parse_class is DemoEnv


def test_stub_policy_rejects_runtime_handler():
    bridge = LatexBridge()

    with pytest.raises(ValueError, match="policy='stub' must not define a runtime handler"):
        bridge.register_spec(
            MacroSpec(
                name="stubbed",
                kind="command",
                parse_class=DemoCommand,
                handler=_noop,
                policy="stub",
            )
        )


def test_duplicate_or_conflicting_macro_specs_fail_fast():
    bridge = LatexBridge()
    bridge.register_spec(
        MacroSpec(
            name="dupe",
            kind="command",
            parse_class=DemoCommand,
            handler=_noop,
            policy="render",
        )
    )

    with pytest.raises(ValueError, match="Duplicate MacroSpec registration"):
        bridge.register_spec(
            MacroSpec(
                name="dupe",
                kind="command",
                parse_class=DemoCommand,
                handler=_noop,
                policy="render",
            )
        )

    with pytest.raises(ValueError, match="Duplicate MacroSpec registration"):
        bridge.register_spec(
            MacroSpec(
                name="dupe",
                kind="env",
                parse_class=DemoEnv,
                handler=_noop,
                policy="render",
            )
        )


def test_validate_macro_registry_detects_wiring_drift():
    bridge = LatexBridge()
    bridge.register_spec(
        MacroSpec(
            name="wired",
            kind="command",
            parse_class=DemoCommand,
            handler=_noop,
            policy="render",
        )
    )

    bridge.command_handlers.pop("wired", None)
    with pytest.raises(ValueError, match="missing command handler wiring"):
        bridge.validate_macro_registry()


def test_table_specs_use_render_handlers_for_table_tabular_and_stub_for_multicolumn():
    table_spec = latex.macro_specs["table"]
    tabular_spec = latex.macro_specs["tabular"]
    multicolumn_spec = latex.macro_specs["multicolumn"]

    assert table_spec.policy == "render"
    assert tabular_spec.policy == "render"
    assert multicolumn_spec.policy == "stub"
    assert table_spec.handler is not None
    assert tabular_spec.handler is not None
    assert multicolumn_spec.handler is None


def test_command_decorator_can_register_through_macro_spec():
    bridge = LatexBridge()

    @bridge.command("decorcmd", inline=True, parse_class=DemoCommand)
    def _handle(_node):
        return None

    assert "decorcmd" in bridge.macro_specs
    spec = bridge.macro_specs["decorcmd"]
    assert spec.kind == "command"
    assert spec.policy == "render"
    assert spec.inline is True


def test_command_decorator_without_parse_class_fails_in_strict_mode():
    bridge = LatexBridge()
    with pytest.raises(ValueError, match="requires parse_class"):
        @bridge.command("legacy")
        def _legacy(_node):
            return None


def test_env_decorator_without_parse_class_fails_in_strict_mode():
    bridge = LatexBridge()
    with pytest.raises(ValueError, match="requires parse_class"):
        @bridge.env("legacyenv")
        def _legacy(_node):
            return None


def test_legacy_decorator_registration_can_be_enabled_explicitly():
    bridge = LatexBridge(strict_macro_specs=False)

    @bridge.command("legacy")
    def _legacy_cmd(_node):
        return None

    @bridge.env("legacyenv")
    def _legacy_env(_node):
        return None

    assert "legacy" in bridge.command_handlers
    assert "legacyenv" in bridge.env_handlers
    assert "legacy" not in bridge.macro_specs
    assert "legacyenv" not in bridge.macro_specs


def test_env_decorator_can_register_through_macro_spec():
    bridge = LatexBridge()

    @bridge.env("decorenv", parse_class=DemoEnv)
    def _handle(_node):
        return None

    assert "decorenv" in bridge.macro_specs
    spec = bridge.macro_specs["decorenv"]
    assert spec.kind == "env"
    assert spec.policy == "render"


def test_global_registry_has_no_legacy_handler_or_macro_wiring_drift():
    specs = set(latex.macro_specs)
    assert set(latex.command_handlers) - specs == set()
    assert set(latex.env_handlers) - specs == set()
    assert set(latex.macro_handlers) - specs == set()
    assert latex.macro_specs["color"].policy == "declaration"


def test_comment_directive_registration_is_deduplicated_and_normalized():
    bridge = LatexBridge()
    bridge.register_comment_directive(
        path_pattern=r"figure\.wrap\.(?:shift\.[xy]|gap)",
        macro_name=r"\DocxlateFigWrapSet",
    )
    bridge.register_comment_directive(
        path_pattern=r"figure\.wrap\.(?:shift\.[xy]|gap)",
        macro_name=r"\DocxlateFigWrapSet",
    )

    assert len(bridge._directive_rules) == 1
    pattern, macro_name = bridge._directive_rules[0]
    assert pattern.fullmatch("FIGURE.WRAP.GAP")
    assert macro_name == "DocxlateFigWrapSet"


def test_global_registry_wires_figure_wrap_comment_directive():
    assert any(
        macro_name == "docxlatefigwrapset" and pattern.fullmatch("figure.wrap.shift.y")
        for pattern, macro_name in latex._directive_rules
    )
