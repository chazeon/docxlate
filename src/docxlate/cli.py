import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import shutil
import xml.etree.ElementTree as ET

import click
import yaml
from pydantic import ValidationError
from .config import validate_runtime_config
from .handlers import latex


def _write_docx_with_replaced_styles(docx_path: Path, styles_xml_path: Path):
    styles_bytes = styles_xml_path.read_bytes()
    try:
        root = ET.fromstring(styles_bytes)
    except ET.ParseError as exc:
        raise click.ClickException(
            f"Invalid styles XML at {styles_xml_path}: {exc}"
        ) from exc
    if root.tag.rsplit("}", 1)[-1] != "styles":
        raise click.ClickException(
            f"Invalid styles XML at {styles_xml_path}: root element must be <w:styles>"
        )

    with NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp_path = Path(tmp.name)
    try:
        with ZipFile(docx_path, "r") as zin, ZipFile(tmp_path, "w", ZIP_DEFLATED) as zout:
            replaced = False
            for item in zin.infolist():
                if item.filename == "word/styles.xml":
                    zout.writestr(item, styles_bytes)
                    replaced = True
                else:
                    zout.writestr(item, zin.read(item.filename))
            if not replaced:
                raise click.ClickException(
                    f"Could not find word/styles.xml in {docx_path}"
                )
        shutil.move(str(tmp_path), str(docx_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _dump_styles_from_docx(docx_path: Path, output_styles_path: Path):
    with ZipFile(docx_path, "r") as zin:
        try:
            styles_bytes = zin.read("word/styles.xml")
        except KeyError as exc:
            raise click.ClickException(
                f"Could not find word/styles.xml in {docx_path}"
            ) from exc
    output_styles_path.write_bytes(styles_bytes)

@click.command()
@click.argument("tex_path", type=click.Path(exists=True))
@click.option("-o", "--output", default="output.docx", help="Output Docx file")
@click.option(
    "-t",
    "--template",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Optional DOCX template to use as output base document; .xml path is treated as styles.xml",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Optional YAML config file for runtime settings",
)
@click.option(
    "--styles-xml",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Optional styles.xml to inject into output DOCX after rendering",
)
@click.option(
    "--dump-styles",
    type=click.Path(dir_okay=False),
    default=None,
    help="Optional path to write effective output styles.xml",
)
def main(tex_path, output, template, config, styles_xml, dump_styles):
    
    try:
        template_path = Path(template) if template else None
        styles_xml_path = Path(styles_xml) if styles_xml else None
        if template_path and template_path.suffix.lower() == ".xml":
            if styles_xml_path is not None:
                raise click.ClickException(
                    "Use either --template <styles.xml> or --styles-xml, not both."
                )
            styles_xml_path = template_path
            template_path = None

        latex.reset_document(str(template_path) if template_path else None)
        with open(tex_path, 'r') as f:
            tex_content = f.read()

        config_path = Path(config) if config else Path.cwd() / "docxlate.yaml"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as cf:
                loaded = yaml.safe_load(cf) or {}
            if not isinstance(loaded, dict):
                raise ValueError("YAML config must be a mapping at top level")
            try:
                latex.context.update(validate_runtime_config(loaded))
            except ValidationError as exc:
                raise click.ClickException(f"Invalid config at {config_path}: {exc}") from exc

        latex.context['tex_path'] = tex_path  # Store the path for potential .aux loading in handlers
        latex.run(tex_content)
        output_path = Path(output)
        latex.save(output_path)
        if styles_xml_path is not None:
            _write_docx_with_replaced_styles(output_path, styles_xml_path)
        if dump_styles:
            _dump_styles_from_docx(output_path, Path(dump_styles))
        print(f"Successfully converted {tex_path} to {output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise e
        sys.exit(1)

if __name__ == "__main__":
    main()
