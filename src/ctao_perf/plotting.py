"""Shared matplotlib styling and plotting helpers."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

COLORS = ["#333333", "#c0254b", "#4a7fd6", "#e8962e", "#2a9d6f", "#7d4fb0"]
MARKERS = ["o", "s", "v", "D", "^", "P"]
LINESTYLES = ["-", (0, (2, 1)), (0, (1, 1)), (0, (4, 1, 1, 1)), (0, (5, 2)), "-."]

STYLE = {
    "figure.dpi": 100,
    "savefig.dpi": 150,
    "font.size": 12,
    "axes.labelsize": 13,
    "legend.fontsize": 12,
    "legend.frameon": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
}

E_RECO_LABEL = r"Reconstructed gamma-ray energy $E_\mathrm{R}$ [TeV]"
E_TRUE_LABEL = r"True gamma-ray energy $E_\mathrm{T}$ [TeV]"
SENS_LABEL = r"E$^2$ $\times$ Flux Sensitivity [erg cm$^{-2}$ s$^{-1}$]"


def new_figure(size=(8, 5.2)):
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=size)
    return fig, ax


def apply_style(ax):
    ax.tick_params(which="both", direction="in", top=True, right=True)


CREDITS = {
    "gammapy": "reproduced with gammapy from doi:{doi} ({name})",
    "root": "official curves from the ROOT files of doi:{doi} ({name})",
}


def credit(ax, release, source="gammapy"):
    ax.text(
        1.015, 0.5,
        CREDITS[source].format(doi=release.doi, name=release.name),
        transform=ax.transAxes, rotation=90, va="center", fontsize=7, color="#555555",
    )


def binned_points(ax, edges, values, i=0, label=None, open_marker=False, **kwargs):
    """Points with horizontal bars spanning each energy bin; NaNs are skipped."""
    edges = np.asarray(edges, dtype=float)
    values = np.asarray(values, dtype=float)
    lo, hi = edges[:-1], edges[1:]
    c = np.sqrt(lo * hi)
    ok = np.isfinite(values)
    color = kwargs.pop("color", COLORS[i % len(COLORS)])
    ax.errorbar(
        c[ok], values[ok], xerr=[c[ok] - lo[ok], hi[ok] - c[ok]],
        fmt=MARKERS[i % len(MARKERS)], color=color, mfc="white" if open_marker else color,
        capsize=0, lw=2, ms=6, label=label, **kwargs,
    )


def finish(fig, ax, release, source="gammapy"):
    apply_style(ax)
    credit(ax, release, source)
    fig.tight_layout()
    return fig


def draw_curve(ax, curve, i=0, open_marker=False, **kwargs):
    """Draw a :class:`~ctao_perf.curves.Curve`: a point with a bar per bin, or a line."""
    color = kwargs.pop("color", COLORS[i % len(COLORS)])
    y = curve.y
    ok = np.isfinite(y)
    if curve.is_binned:
        ax.errorbar(
            curve.x[ok], y[ok], xerr=[(curve.x - curve.xlo)[ok], (curve.xhi - curve.x)[ok]],
            fmt=MARKERS[i % len(MARKERS)], color=color, mfc="white" if open_marker else color,
            capsize=0, lw=2, ms=6, label=curve.label or None, **kwargs,
        )
    else:
        kwargs.setdefault("ls", LINESTYLES[i % len(LINESTYLES)])
        ax.plot(curve.x[ok], y[ok], color=color, lw=2.5, label=curve.label or None, **kwargs)
