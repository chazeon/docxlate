from __future__ import annotations

import pytest
from plasTeX import Command, Environment

from docxlate.core import LatexBridge
from docxlate.extensions.table.runtime import table_specs
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


def test_table_specs_are_explicit_parse_only_stubs():
    specs = table_specs()
    names = {spec.name: spec for spec in specs}

    assert set(names.keys()) == {"table", "tabular", "multicolumn"}
    assert all(spec.policy == "stub" for spec in specs)
    assert all(spec.parse_class is not None for spec in specs)
    assert all(spec.handler is None for spec in specs)


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


def test_env_decorator_can_register_through_macro_spec():
    bridge = LatexBridge()

    @bridge.env("decorenv", parse_class=DemoEnv)
    def _handle(_node):
        return None

    assert "decorenv" in bridge.macro_specs
    spec = bridge.macro_specs["decorenv"]
    assert spec.kind == "env"
    assert spec.policy == "render"
