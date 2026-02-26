# Directives

Directives allow you to provide one-off overrides for the conversion process directly within your LaTeX source code. They are implemented as special LaTeX comments that `docxlate` identifies during tokenization.

## Syntax

A directive must be placed on its own line and follow this format:

```latex
% docxlate: <key>=<value>
```

- **Keys** are case-insensitive and usually follow a hierarchical path.
- **Values** for layout directives are typically numbers representing inches.

## Figure & Wrapfigure Directives

These directives must be placed **inside** a `wrapfigure` environment to take effect. They allow you to fine-tune the placement and spacing of specific floating figures without changing global configuration.

### Vertical Shift

Adjust the vertical position of the figure. A positive value moves the figure down.

- `figure.wrap.shift.y`: Vertical shift in inches.

### Spacing & Gaps

- `figure.wrap.gap`: The vertical gap between the image and its caption (in inches).

### Padding (Wrap Distances)

Control the distance between the wrapped figure and the surrounding document text.

- `figure.wrap.pad.left`: Left padding in inches.
- `figure.wrap.pad.right`: Right padding in inches.
- `figure.wrap.pad.top`: Top padding in inches.
- `figure.wrap.pad.bottom`: Bottom padding in inches.

### Insets

Control the internal margins of the textbox containing the figure and caption.

- `figure.wrap.inset.left`: Left inset in inches.
- `figure.wrap.inset.right`: Right inset in inches.
- `figure.wrap.inset.top`: Top inset in inches.
- `figure.wrap.inset.bottom`: Bottom inset in inches.

## Example

```latex
\begin{wrapfigure}{r}{0.4\textwidth}
  % Shift this specific figure down by 0.2 inches
  % docxlate: figure.wrap.shift.y=0.2
  % Increase the padding on the left
  % docxlate: figure.wrap.pad.left=0.2
  % Override the caption gap
  % docxlate: figure.wrap.gap=0.1
  \includegraphics{my-figure.png}
  \caption{A precisely placed figure.}
\end{wrapfigure}
```

## Warnings

If a directive is found outside of a supported context (e.g., a `figure.wrap.*` directive outside of a `wrapfigure` environment), `docxlate` will emit a warning and ignore the directive.
