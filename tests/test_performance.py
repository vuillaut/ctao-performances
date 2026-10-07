from pathlib import Path

import astropy.units as u
import numpy as np
import pytest
from gammapy.irf import EnergyDispersion2D
from gammapy.maps import MapAxis

from ctao_perf import load_release
from ctao_perf import performance as perf
from ctao_perf.irfs import IRFLibrary, fill_edisp

DATA_DIR = Path("data")


def test_fill_edisp():
    e = MapAxis.from_energy_bounds(1 * u.TeV, 100 * u.TeV, nbin=4, name="energy_true")
    m = MapAxis.from_edges(np.linspace(0, 2, 5), name="migra")
    o = MapAxis.from_edges([0, 1, 2] * u.deg, name="offset")
    data = np.zeros((4, 4, 2))
    data[:2, 1:3, :] = 0.5  # two highest energies empty
    filled = fill_edisp(EnergyDispersion2D(axes=[e, m, o], data=data))
    assert np.allclose(filled.data[3], data[1])
    assert np.allclose(filled.data[:2], data[:2])


def test_log_energy_axis():
    axis = perf.log_energy_axis()
    assert axis.nbin == 21
    assert np.isclose(axis.edges[0].to_value("TeV"), 10**-1.9)
    assert np.allclose(np.diff(np.log10(axis.edges.value)), 0.2)


def _library(name):
    release = load_release(name)
    lib = IRFLibrary(release, DATA_DIR)
    if not lib.exists("South", release.reference_duration):
        pytest.skip(f"{name} IRFs not downloaded")
    return release, lib


@pytest.mark.data
def test_prod5_south_sensitivity_minimum():
    """Official prod5 South 50 h minimum is ~0.93e-13 erg cm-2 s-1 around 4 TeV."""
    release, lib = _library("prod5-v0.1")
    _, e2, _ = perf.sensitivity(lib.load("South", 180000), 50 * u.h, location="ctao_south")
    assert 0.8e-13 < np.nanmin(e2) < 1.2e-13


@pytest.mark.data
def test_prod6_sensitivity_matches_tabulated():
    release, lib = _library("prod6-v1.0")
    for site in release.sites:
        e_edges, _, table = lib.provided_sensitivity(site, 180000)
        axis = MapAxis.from_energy_edges(e_edges, name="energy")
        _, ours, _ = perf.sensitivity(
            lib.load(site, 180000), 50 * u.h, location=release.sites[site].location,
            energy_axis=axis,
        )
        sel = (axis.center > 0.1 * u.TeV) & (axis.center < 50 * u.TeV)
        ratio = ours[sel] / table[0][sel]
        assert np.all((ratio > 0.9) & (ratio < 1.3)), (site, ratio)


@pytest.mark.data
def test_prod6_angular_resolution():
    """Official Prod6 South 50 h angular resolution is ~0.052 deg at 1 TeV."""
    release, lib = _library("prod6-v1.0")
    r68 = perf.angular_resolution(lib.load("South", 180000), [1] * u.TeV)
    assert 0.045 < r68[0] < 0.06
