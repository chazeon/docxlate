# Figures & Layout

`docxlate` provides robust support for images and captions, including floating figures.

## Supported Environments

- **`figure`**: Standard LaTeX figures.
- **`wrapfigure`**: Figures that allow text to wrap around them.

## Image Handling

- **Automatic Resolution**: `docxlate` searches for image files specified in `\includegraphics`.
- **Sizing**: Basic support for `width`, `height`, and `scale` options in `\includegraphics`.
- **Graceful Degradation**: If an image file is missing, the caption and a warning placeholder are preserved in the Word document.

## Captions

- **Semantic Roles**: Captions are assigned a specific Word style (usually `Caption`) for consistent formatting.
- **Templating**: Customize the caption prefix (e.g., "Figure 1:") using `plugins.figure.caption.template`.
- **Rich Content**: Captions can contain math, inline styles, and references, which are all rendered correctly.

## Floating and Wrapping

Word handles floating objects differently than LaTeX. `docxlate` uses advanced OOXML extensions to bridge this gap:

- **Anchoring**: Figures are anchored to the paragraph where they appear in the LaTeX source.
- **Wrap Side**: `wrapfigure` alignments (`l`, `r`, etc.) are mapped to Word wrapping properties.
- **Fine-grained Control**: Use [Directives](../03_directives.md) in LaTeX comments for precise control over margins, padding, and vertical shifts for specific figures.
