import sys
from pathlib import Path

import click
import yaml
from pydantic import ValidationError
from .config import validate_runtime_config
from .handlers import latex

@click.command()
@click.argument("tex_path", type=click.Path(exists=True))
@click.option("-o", "--output", default="output.docx", help="Output Docx file")
@click.option(
    "-t",
    "--template",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Optional DOCX template to use as the output base document",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Optional YAML config file for runtime settings",
)
def main(tex_path, output, template, config):
    
    try:
        latex.reset_document(template)
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
        latex.save(output)
        print(f"Successfully converted {tex_path} to {output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise e
        sys.exit(1)

if __name__ == "__main__":
    main()
