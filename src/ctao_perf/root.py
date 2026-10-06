"""Official curves stored in the ROOT files of a release.

Each ROOT file holds histograms (``TH1F``, ``TH2F``, ...) produced by the CTAO analysis for one
IRF: ``DiffSens``, ``AngResEtrue``, ``ERes``, ``EffectiveArea``, ``BGRatePerSqDeg``, ... The
energy axis of all of them is log10(E/TeV). They are read with ``uproot``, no ROOT install is
needed. See ``docs/data/root-files.md``.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np

from .config import Release
from .curves import Curve
from .download import root_dir

log = logging.getLogger(__name__)

UNITS = {
    "DiffSens": "erg cm-2 s-1",
    "AngResEtrue": "deg",
    "AngRes": "deg",
    "ERes": "",
    "EffectiveArea": "m2",
    "EffectiveAreaNoTheta2cut": "m2",
    "BGRatePerSqDeg": "Hz deg-2",
}


class RootLibrary:
    """Access to the ROOT files of one release, resolved from its file-name pattern."""

    def __init__(self, release: Release, data_dir):
        self.release = release
        self.directory = root_dir(release, data_dir)

    def available(self) -> bool:
        """ROOT files are configured for the release and downloaded."""
        return (bool(self.release.zenodo_root_file) and self.directory.is_dir()
                and any(self.directory.glob("*.root")))

    def path(self, site, duration, **selection) -> Path:
        path = self.directory / self.release.root_irf_filename(site, duration, **selection)
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found; run `ctao-perf download --root {self.release.name}`"
            )
        return path

    def exists(self, site, duration, **selection) -> bool:
        return (self.directory / self.release.root_irf_filename(site, duration, **selection)).exists()


@lru_cache(maxsize=128)
def read_histogram(path, name):
    """``(values, *edges)`` of a histogram, without under/overflow bins.

    1-D: ``(values, x_edges)``; 2-D: ``(values[x, y], x_edges, y_edges)``.
    """
    import uproot

    with uproot.open(path) as f:
        if name not in f:
            raise KeyError(f"{name} not in {path}; histograms: {sorted(f.keys(cycle=False))[:12]}...")
        return f[name].to_numpy()


def _energy_edges_tev(log_edges):
    return 10.0 ** np.asarray(log_edges, dtype=float)


def _curve(path, name, label="", positive=True):
    values, log_e = read_histogram(path, name)
    curve = Curve.binned(_energy_edges_tev(log_e), values, label)
    return curve.positive() if positive else curve


def differential_sensitivity(path) -> Curve:
    """``DiffSens``: E2 dN/dE in erg cm-2 s-1, five bins per decade of reconstructed energy."""
    return _curve(path, "DiffSens")


def differential_sensitivity_offaxis(path):
    """``DiffSens_offaxis``: ``(offset_edges_deg, energy_edges_tev, values[offset, energy])``."""
    values, log_e, theta = read_histogram(path, "DiffSens_offaxis")
    values = np.where(values > 0, values, np.nan).T
    return np.asarray(theta, dtype=float), _energy_edges_tev(log_e), values


def angular_resolution(path, containment=68, energy="true") -> Curve:
    """68 % (or 80, 95) containment radius in degrees, vs true or reconstructed energy."""
    suffix = "" if containment == 68 else str(containment)
    name = ("AngResEtrue" if energy == "true" else "AngRes") + suffix
    return _curve(path, name)


def energy_resolution(path) -> Curve:
    """``ERes``, the energy resolution (labelled "RMS" in the file, see the docs)."""
    return _curve(path, "ERes")


def effective_area(path, direction_cut=False) -> Curve:
    """Effective area in m2 vs true energy, after gamma/hadron cuts.

    ``direction_cut=False`` reads ``EffectiveAreaNoTheta2cut`` (no cut on the reconstructed
    direction), ``True`` reads ``EffectiveArea`` (with the optimised direction cut).
    """
    name = "EffectiveArea" if direction_cut else "EffectiveAreaNoTheta2cut"
    values, log_e = read_histogram(path, name)
    edges = _energy_edges_tev(log_e)
    return Curve(np.sqrt(edges[:-1] * edges[1:]), values).positive()


def background_rate(path) -> Curve:
    """``BGRatePerSqDeg``: residual background in Hz deg-2 per bin of reconstructed energy."""
    return _curve(path, "BGRatePerSqDeg")
