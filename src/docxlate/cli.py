import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import shutil
import xml.etree.ElementTree as ET
from io import BytesIO

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


def _write_docx_with_replaced_part(docx_path: Path, part_path: str, xml_path: Path):
    xml_bytes = xml_path.read_bytes()
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise click.ClickException(f"Invalid XML at {xml_path}: {exc}") from exc

    expected_roots = {
        "word/styles.xml": "styles",
        "word/theme/theme1.xml": "theme",
        "word/fontTable.xml": "fonts",
        "word/numbering.xml": "numbering",
        "word/settings.xml": "settings",
    }
    expected_root = expected_roots.get(part_path)
    if expected_root and root.tag.rsplit("}", 1)[-1] != expected_root:
        raise click.ClickException(
            f"Invalid XML at {xml_path}: expected <w:{expected_root}> root for {part_path}"
        )

    with NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp_path = Path(tmp.name)
    try:
        with ZipFile(docx_path, "r") as zin, ZipFile(tmp_path, "w", ZIP_DEFLATED) as zout:
            replaced = False
            for item in zin.infolist():
                if item.filename == part_path:
                    zout.writestr(item, xml_bytes)
                    replaced = True
                else:
                    zout.writestr(item, zin.read(item.filename))
            if not replaced:
                raise click.ClickException(f"Could not find {part_path} in {docx_path}")
        shutil.move(str(tmp_path), str(docx_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _format_xml_bytes(data: bytes) -> bytes:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.fromstring(data, parser=parser)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    buffer = BytesIO()
    tree.write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue()


def _dump_part_from_docx(docx_path: Path, part_path: str, output_path: Path):
    with ZipFile(docx_path, "r") as zin:
        try:
            data = zin.read(part_path)
        except KeyError as exc:
            raise click.ClickException(
                f"Could not find {part_path} in {docx_path}"
            ) from exc
    output_path.write_bytes(_format_xml_bytes(data))


def _resolve_template_chain(
    templates: tuple[str, ...], styles_xml: str | None
) -> tuple[Path | None, list[Path]]:
    base_template: Path | None = None
    overrides: list[Path] = []
    for raw in templates:
        p = Path(raw)
        suffix = p.suffix.lower()
        if suffix == ".docx":
            base_template = p
            continue
        if suffix == ".xml":
            overrides.append(p)
            continue
        raise click.ClickException(
            f"Unsupported template override type: {p}. Use .docx or .xml."
        )
    if styles_xml:
        overrides.append(Path(styles_xml))
    return base_template, overrides


def _apply_xml_overrides(docx_path: Path, overrides: list[Path]):
    part_map = {
        "styles.xml": "word/styles.xml",
        "theme1.xml": "word/theme/theme1.xml",
        "fonttable.xml": "word/fontTable.xml",
        "numbering.xml": "word/numbering.xml",
        "settings.xml": "word/settings.xml",
    }
    for override in overrides:
        part = part_map.get(override.name.lower())
        if part is None:
            raise click.ClickException(
                f"Unknown XML override name: {override.name}. "
                f"Supported: {', '.join(sorted(part_map))}"
            )
        _write_docx_with_replaced_part(docx_path, part, override)

@click.group()
def cli():
    """docxlate command group."""


@cli.command(name="convert")
@click.argument("tex_path", type=click.Path(exists=True))
@click.option("-o", "--output", default="output.docx", help="Output Docx file")
@click.option(
    "-t",
    "--template",
    type=click.Path(exists=True, dir_okay=False),
    multiple=True,
    help="Template override chain; accepts .docx base and/or XML overrides (styles.xml, theme1.xml, fontTable.xml, numbering.xml, settings.xml). Later values override earlier.",
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
def convert_main(tex_path, output, template, config, styles_xml):
    
    try:
        base_template, xml_overrides = _resolve_template_chain(template, styles_xml)
        latex.reset_document(str(base_template) if base_template else None)
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
        if xml_overrides:
            _apply_xml_overrides(output_path, xml_overrides)
        print(f"Successfully converted {tex_path} to {output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise e
        sys.exit(1)

@cli.command(name="dump-styles")
@click.argument("docx_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False),
    default="styles.xml",
    show_default=True,
    help="Output styles.xml path",
)
def dump_styles_main(docx_path, output):
    _dump_part_from_docx(Path(docx_path), "word/styles.xml", Path(output))
    click.echo(f"Wrote styles XML to {output}")


@cli.command(name="dump-theme")
@click.argument("docx_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False),
    default="theme1.xml",
    show_default=True,
    help="Output theme XML path",
)
def dump_theme_main(docx_path, output):
    _dump_part_from_docx(Path(docx_path), "word/theme/theme1.xml", Path(output))
    click.echo(f"Wrote theme XML to {output}")


@cli.command(name="dump-font-table")
@click.argument("docx_path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False),
    default="fontTable.xml",
    show_default=True,
    help="Output font table XML path",
)
def dump_font_table_main(docx_path, output):
    _dump_part_from_docx(Path(docx_path), "word/fontTable.xml", Path(output))
    click.echo(f"Wrote font table XML to {output}")


if __name__ == "__main__":
    cli()
