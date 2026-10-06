"""A plotted curve, as plain arrays: the common currency of sources, figures and ASCII files."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

import numpy as np


@dataclass
class Curve:
    """One series of points.

    ``x`` and ``y`` are plain floats in the units of the figure axes (TeV, erg cm-2 s-1,
    deg, m2, Hz deg-2, ...). If ``xlo``/``xhi`` are set, each point is a bin (drawn as a
    point with a horizontal bar); otherwise the curve is drawn as a line.
    """

    x: np.ndarray
    y: np.ndarray
    xlo: np.ndarray | None = None
    xhi: np.ndarray | None = None
    label: str = ""

    def __post_init__(self):
        self.x = np.asarray(self.x, dtype=float)
        self.y = np.asarray(self.y, dtype=float)
        if self.xlo is not None:
            self.xlo = np.asarray(self.xlo, dtype=float)
            self.xhi = np.asarray(self.xhi, dtype=float)

    @classmethod
    def binned(cls, edges, y, label=""):
        """Bins given by their ``edges`` (one more than ``y``); x is the geometric centre."""
        edges = np.asarray(edges, dtype=float)
        lo, hi = edges[:-1], edges[1:]
        return cls(np.sqrt(lo * hi), y, lo, hi, label)

    @property
    def is_binned(self):
        return self.xlo is not None

    @property
    def name(self):
        """Label turned into a token without spaces, used in the ASCII files."""
        return re.sub(r"[^A-Za-z0-9.+-]+", "_", self.label).strip("_") or "curve"

    def with_label(self, label):
        return replace(self, label=label)

    def masked(self, mask):
        """Copy with ``y`` set to NaN where ``mask`` is true."""
        y = self.y.copy()
        y[np.asarray(mask)] = np.nan
        return replace(self, y=y)

    def positive(self):
        """Copy with non-finite or non-positive ``y`` set to NaN (for log axes)."""
        y = self.y.copy()
        y[~np.isfinite(y) | (y <= 0)] = np.nan
        return replace(self, y=y)
