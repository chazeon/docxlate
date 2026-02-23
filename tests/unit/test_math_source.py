from plasTeX.TeX import TeX

from docxlate.handlers import latex


def _first_named_node(tex_source: str, name: str):
    tex = TeX()
    tex.input(tex_source)
    doc = tex.parse()
    for node in doc.childNodes:
        if getattr(node, "nodeName", None) == name:
            return node
    raise AssertionError(f"Node {name!r} not found")


def test_equation_math_source_preserves_superscript_syntax():
    node = _first_named_node(r"\begin{equation}E=mc^2\end{equation}", "equation")

    assert latex.get_math_source(node) == "E=mc^2"


def test_inline_math_source_strips_dollar_delimiters():
    node = _first_named_node(r"$a^2+b^2=c^2$", "math")

    assert latex.get_math_source(node) == "a^2+b^2=c^2"
