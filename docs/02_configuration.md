# Configuration

`docxlate` can be configured using a YAML file. By default, it looks for a file named `docxlate.yaml` in the current directory. You can also specify a custom config file using the `--config` flag.

## Runtime Configuration

The top-level configuration keys are:

- `title_render_policy`: `explicit` | `auto` | `always`
    - `explicit`: Only render title if `\maketitle` is present.
    - `auto`: Render title if metadata (`\title`, `\author`) is found.
    - `always`: Always try to render a title block.
- `parse_skip_packages`: (List of Strings) LaTeX package names to ignore during parsing.
- `parse_skip_usepackage_paths`: (List of Strings) Specific paths in `\usepackage{...}` to skip.
- `mathml2omml_xsl_path`: (String) Absolute path to the `mathml2omml.xsl` file for high-quality math.
- `unknown_macro_policy`: `warn` | `strict`
    - `warn` (default): preserve child content and emit one warning per unknown macro name.
    - `strict`: fail conversion on the first unknown macro encountered.
- `unknown_macro_allowlist`: (List of Strings) Macro names that are exempt from unknown-macro warnings/errors.
- `plugins`: (Mapping) Plugin-specific configurations.

## Plugins

`docxlate` uses a modular plugin system for its major features. Each plugin has its own configuration block under the `plugins` key.

### Bibliography Plugin (`plugins.bibliography`)

Handles citation formatting and bibliography generation.

- `template`: (String) Jinja2 template for rendering bibliography entries.
- `numbering`: `bracket` | `none`. Default is `bracket`.
- `indent_in`: (Float, > 0) Indentation for bibliography entries in inches. Default is `0.35`.
- `et_al_limit`: (Int, > 0) Number of authors before "et al." is used. Default is `3`.
- `macro_replacements`: (Mapping) Map of LaTeX macros to their replacement strings when used within bibliography entries.
- `citation_compress_ranges`: (Bool) Whether to compress numeric citation ranges (e.g., `[1, 2, 3]` -> `[1-3]`).
- `citation_range_min_run`: (Int, > 1) Minimum number of consecutive citations to form a range. Default is `2`.
- `missing_entry_policy`: `hole` | `key`. Policy for citations not found in artifacts.
    - `key`: Show the citation key (e.g., `[MyPaper2024]`).
    - `hole`: Show a placeholder (e.g., `[?]`).

### Figure Plugin (`plugins.figure`)

Handles both standard `figure` and `wrapfigure` environments.

#### Caption Settings (`plugins.figure.caption`)
- `template`: (String) Jinja2 template for captions. Available variables: `fig_name`, `fig_num`, `caption`.

#### Image Settings (`plugins.figure.image`)
- `kind`: `inline` | `wrap`. Default placement strategy.
- `wrap`: (Mapping) Configuration for wrapped/floating images.
    - `caption_anchor`: `group` | `separate`.
        - `group`: Anchor image and caption together in one floating group (default).
        - `separate`: Anchor them independently.
    - `gap`: (Float, >= 0) Gap between image and caption in inches. Default is `0.045` (114300 EMU).
    - `pad`: (Edges) Padding around the wrapped figure.
        - **Number**: Set all sides to the same value (e.g., `0.2`).
        - **List**: `[top, right, bottom, left]` (e.g., `[0.1, 0.2, 0.1, 0.2]`).
        - **Mapping**: `{top: 0.1, right: 0.2, bottom: 0.1, left: 0.2}`. Short keys `{t, r, b, l}` are also supported.
    - `inset`: (Edges) Insets for the textbox containing the figure. Same format as `pad`.
    - `shift`: (Point) Positional shift for the figure.
        - **Number**: Set vertical (`y`) shift (e.g., `0.05`).
        - **List**: `[x, y]` (e.g., `[0, 0.05]`).
        - **Mapping**: `{x: 0, y: 0.05}`.

## Example `docxlate.yaml`

```yaml
title_render_policy: explicit
parse_skip_packages:
  - fontspec
  - expl3
mathml2omml_xsl_path: /Applications/Microsoft Word.app/Contents/Resources/mathml2omml.xsl
unknown_macro_policy: warn
unknown_macro_allowlist:
  - providecommand
  - newcommand

plugins:
  bibliography:
    citation_compress_ranges: true
    citation_range_min_run: 2
    missing_entry_policy: key
  figure:
    caption:
      template: "\\textbf{<< fig_name >>. << fig_num >>} << caption >>"
    image:
      wrap:
        gap: 0.1
        pad: 0.2
        shift:
          y: 0.05
```

## Advanced Customization

For one-off overrides of figure placement directly in your LaTeX source, see [Directives](03_directives.md).
