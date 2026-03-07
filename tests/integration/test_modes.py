from docxlate.handlers import latex


def test_unknown_macro_permissive_vs_strict_modes():
    tex = r"Before \unknownmacro{value} after"

    latex.context["mode"] = "permissive"
    latex.run(tex)
    permissive_text = "\n".join(p.text for p in latex.doc.paragraphs)
    warnings = latex.context.get("warnings", [])

    latex.reset_document()
    latex.context.clear()
    latex.context["mode"] = "strict"

    try:
        latex.run(tex)
    except ValueError:
        pass
    else:
        raise AssertionError("strict mode should fail on unknown macros")

    assert "Before" in permissive_text
    assert "value" in permissive_text
    assert "after" in permissive_text
    assert any("Unknown LaTeX command: \\unknownmacro" in w for w in warnings)


def test_unknown_macro_allowlist_suppresses_warning():
    tex = r"Before \unknownmacro{value} after"
    latex.context["unknown_macro_policy"] = "warn"
    latex.context["unknown_macro_allowlist"] = ["unknownmacro"]
    latex.run(tex)

    text = "\n".join(p.text for p in latex.doc.paragraphs)
    warnings = latex.context.get("warnings", [])
    assert "Before" in text
    assert "value" in text
    assert "after" in text
    assert not any("Unknown LaTeX command: \\unknownmacro" in w for w in warnings)
