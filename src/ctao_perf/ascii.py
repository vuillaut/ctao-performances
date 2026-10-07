"""Plain-text data files for each figure, and a snippet that plots them again."""

from __future__ import annotations

from textwrap import dedent

import numpy as np

COLUMNS = ("series", "x", "xlo", "xhi", "y")


def series_names(curves) -> list[str]:
    """One distinct token per curve: ``Curve.name``, with ``_2``, ``_3``... added on repeats."""
    seen, names = {}, []
    for c in curves:
        n = seen.get(c.name, 0) + 1
        seen[c.name] = n
        names.append(c.name if n == 1 else f"{c.name}_{n}")
    return names


def _fmt(v):
    return "nan" if v is None or not np.isfinite(v) else f"{v:.6e}"


def ascii_table(result, header_lines=()) -> str:
    """Whitespace-separated table of every finite point of every curve of a figure.

    Columns: ``series x xlo xhi y`` (the last comment line repeats the names). ``xlo``/``xhi`` are the bin edges (``nan`` for curves
    that are not binned). ``series`` is a token without spaces; the header maps it to the
    legend label.
    """
    lines = [f"# {result.title}"]
    lines += [f"# {h}" for h in header_lines]
    lines += [
        f"# x: {result.xlabel}",
        f"# y: {result.ylabel}",
        "# series (token = legend label):",
    ]
    names = series_names(result.curves)
    lines += [f"#   {n} = {c.label}" for n, c in zip(names, result.curves)]
    lines.append("# " + " ".join(COLUMNS))
    for name, c in zip(names, result.curves):
        for i in range(len(c.x)):
            if not np.isfinite(c.y[i]):
                continue
            lo, hi = (c.xlo[i], c.xhi[i]) if c.is_binned else (np.nan, np.nan)
            lines.append(f"{name} {_fmt(c.x[i])} {_fmt(lo)} {_fmt(hi)} {_fmt(c.y[i])}")
    return "\n".join(lines) + "\n"


def plot_snippet(result, data_file) -> str:
    """Python code that reads ``data_file`` and plots the figure again with matplotlib."""
    names = series_names(result.curves)
    series = {n: c.label for n, c in zip(names, result.curves)}
    binned = {n: c.is_binned for n, c in zip(names, result.curves)}
    width = max([1, *map(len, names)])  # the series field must hold the longest token
    hline_code = ("" if result.hline is None
                  else f'ax.axhline({result.hline!r}, color="gray", ls="--", lw=1)\n        ')
    return dedent(f'''\
        import matplotlib.pyplot as plt
        import numpy as np

        columns = [("series", "U{width}"), ("x", float), ("xlo", float), ("xhi", float), ("y", float)]
        data = np.genfromtxt({data_file!r}, dtype=columns, encoding="utf-8")
        labels = {series!r}
        binned = {binned!r}

        fig, ax = plt.subplots(figsize=(8, 5.2))
        for name, label in labels.items():
            s = data[data["series"] == name]
            if binned[name]:  # one point per bin, with a bar spanning the bin
                ax.errorbar(s["x"], s["y"], xerr=[s["x"] - s["xlo"], s["xhi"] - s["x"]],
                            fmt="o", capsize=0, label=label)
            else:
                ax.plot(s["x"], s["y"], label=label)
        ax.set(xscale={result.xscale!r}, yscale={result.yscale!r},
               xlabel={result.xlabel!r}, ylabel={result.ylabel!r})
        {hline_code}ax.legend()
        fig.tight_layout()
        plt.show()
        ''')
