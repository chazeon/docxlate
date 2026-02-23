from pathlib import Path
from docx import Document
from click.testing import CliRunner

from docxlate.cli import main
from docxlate.handlers import latex


def _reset_router():
    latex.reset_document()
    latex.context.clear()


def test_cli_bridge_runs(tmp_path):
    _reset_router()
    tex_path = Path('test.tex')
    latex.context['tex_path'] = str(tex_path)
    latex.run(tex_path.read_text())
    out_path = tmp_path / 'output.docx'
    latex.save(out_path)
    assert out_path.exists()


def test_cli_uses_template_docx(tmp_path):
    runner = CliRunner()
    tex_path = tmp_path / "input.tex"
    tex_path.write_text(r"\section{Intro} Hello from input.")

    template_path = tmp_path / "template.docx"
    template_doc = Document()
    template_doc.add_paragraph("TEMPLATE MARKER")
    template_doc.save(template_path)

    out_path = tmp_path / "output.docx"
    result = runner.invoke(
        main,
        [str(tex_path), "-o", str(out_path), "--template", str(template_path)],
    )

    assert result.exit_code == 0
    assert out_path.exists()
    rendered = Document(out_path)
    text = "\n".join(p.text for p in rendered.paragraphs)
    assert "TEMPLATE MARKER" not in text
    assert "Intro" in text


def test_cli_loads_yaml_config_for_bibliography_template(tmp_path):
    runner = CliRunner()
    tex_path = tmp_path / "doc.tex"
    tex_path.write_text(r"\cite{KeyA}.")
    (tmp_path / "doc.aux").write_text(r"\abx@aux@cite{0}{KeyA}")
    (tmp_path / "doc.bbl").write_text(Path("tests/fixtures/bbl/sample.bbl").read_text())

    config_path = tmp_path / "docxlate.yaml"
    config_path.write_text(
        "\n".join(
            [
                "bibliography_numbering: none",
                "bibliography_template: |",
                "  <% if authors %><< authors|join(\", \") >>.<% endif %>",
                "  <% if fields.journaltitle %> \\textit{<< fields.journaltitle >>}.<% endif %>",
            ]
        ),
        encoding="utf-8",
    )

    out_path = tmp_path / "output.docx"
    result = runner.invoke(
        main,
        [str(tex_path), "-o", str(out_path), "--config", str(config_path)],
    )

    assert result.exit_code == 0
    rendered = Document(out_path)
    text = "\n".join(p.text for p in rendered.paragraphs)
    assert "A sample article" not in text
    assert "Doe, Jane, Roe, John." in text


def test_cli_rejects_invalid_yaml_config(tmp_path):
    runner = CliRunner()
    tex_path = tmp_path / "doc.tex"
    tex_path.write_text("Hello")
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("unknown_option: true\n", encoding="utf-8")

    result = runner.invoke(
        main,
        [str(tex_path), "--config", str(config_path)],
    )

    assert result.exit_code != 0
    assert "Invalid config" in result.output
