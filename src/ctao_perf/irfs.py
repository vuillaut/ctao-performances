"""Locate and load the IRF files of a release."""

from __future__ import annotations

import logging
import warnings
from functools import lru_cache
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.io import fits
from gammapy.irf import EnergyDispersion2D, load_irf_dict_from_file

from .config import Release
from .download import irf_dir

log = logging.getLogger(__name__)


def fill_edisp(edisp: EnergyDispersion2D) -> EnergyDispersion2D:
    """Copy the last populated migration column into empty ones at higher energy.

    Some files (e.g. prod5 North 50 h) have no energy dispersion entries above
    ~120 TeV although the effective area is non-zero there; gammapy would then
    lose those events entirely.
    """
    data = edisp.data.copy()
    for k in range(data.shape[2]):
        last = None
        for i in range(data.shape[0]):
            if data[i, :, k].sum() > 0:
                last = data[i, :, k]
            elif last is not None:
                data[i, :, k] = last
    return EnergyDispersion2D(axes=edisp.axes, data=data, unit=edisp.unit, meta=edisp.meta)


class IRFLibrary:
    """Access to the IRFs of one release, resolved from its file-name pattern."""

    def __init__(self, release: Release, data_dir):
        self.release = release
        self.directory = irf_dir(release, data_dir)

    def path(self, site, duration, **selection) -> Path:
        name = self.release.irf_filename(site, duration, **selection)
        path = self.directory / name
        if not path.exists():
            raise FileNotFoundError(f"{path} not found; run `ctao-perf download {self.release.name}`")
        return path

    def exists(self, site, duration, **selection) -> bool:
        return (self.directory / self.release.irf_filename(site, duration, **selection)).exists()

    def load(self, site, duration, **selection) -> dict:
        """Dict of gammapy IRFs (aeff, psf, edisp, bkg) for one file."""
        return _load(self.path(site, duration, **selection))

    def provided_sensitivity(self, site, duration, **selection):
        """Differential sensitivity tabulated in the file, if any.

        Returns ``(energy_edges, offset_edges, e2dnde[offset, energy])`` with
        e2dnde in erg cm-2 s-1, or ``None`` when the file has no such HDU.
        """
        return _provided_sensitivity(self.path(site, duration, **selection))


@lru_cache(maxsize=64)
def _load(path: Path):
    # Prod6 files also contain a PSF_TABLE HDU; gammapy keeps the triple-Gaussian
    # PSF, which is what we want: the table is not normalised.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        logging.getLogger("gammapy.irf.io").setLevel(logging.ERROR)
        irfs = load_irf_dict_from_file(path)
    irfs["edisp"] = fill_edisp(irfs["edisp"])
    return irfs


@lru_cache(maxsize=64)
def _provided_sensitivity(path: Path):
    with fits.open(path) as hdul:
        hdu = next((h for h in hdul[1:] if h.header.get("HDUCLAS4") == "DIFFSENS_2D"), None)
        if hdu is None:
            return None
        row = hdu.data[0]
        e_edges = np.append(row["ENERG_LO"], row["ENERG_HI"][-1]) * u.TeV
        t_edges = np.append(row["THETA_LO"], row["THETA_HI"][-1]) * u.deg
        values = np.array(row["DIFFSENS"], dtype=float)
        unit = u.Unit(hdu.columns["DIFFSENS"].unit)
    values = (values * unit).to_value("erg cm-2 s-1")
    values[values <= 0] = np.nan
    return e_edges, t_edges, values
