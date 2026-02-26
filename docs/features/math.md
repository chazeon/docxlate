# Math Conversion

`docxlate` converts LaTeX math into native Word Equation objects (OMML). This ensures that math is editable and renders beautifully within Word.

## How it Works

The conversion process involves three steps:

1.  **LaTeX to MathML**: The LaTeX math source is converted to MathML using the `latex2mathml` library.
2.  **MathML to OMML**: The MathML is transformed into Office Math Markup Language (OMML) using an XSLT transform.
3.  **Injection**: The resulting OMML is injected into the Word document's XML structure using `lxml` and `python-docx` extensions.

## Requirements

The XSLT transform requires a `mathml2omml.xsl` file. This file is not bundled with `docxlate` but is typically included with Microsoft Office installations.

You must provide the path to this file in your [configuration](../02_configuration.md):

```yaml
mathml2omml_xsl_path: /path/to/mathml2omml.xsl
```

## Features

- **Inline Math**: Supports `$ ... $` and `\( ... \)`.
- **Display Math**: Supports `\[ ... \]`, `equation`, `equation*`, and `align` environments.
- **Equation Numbering**: If an equation has a `\label` and a corresponding entry exists in the `.aux` file, the exact equation number from the LaTeX run is preserved in Word.
- **Color Support**: Math color is propagated from LaTeX styles to the OMML output.

## Fallback Behavior

If the XSLT transform file is missing or the conversion fails, `docxlate` will:
1.  Emit a warning diagnostic.
2.  Render the raw LaTeX math source as plain text in the document so you don't lose the content.
