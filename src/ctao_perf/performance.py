"""Performance quantities computed from a dict of gammapy IRFs.

All functions are independent of any release: they take IRFs (as returned by
``gammapy.irf.load_irf_dict_from_file``) and return plain numpy arrays or
astropy quantities.
"""

from __future__ import annotations

import warnings

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from gammapy.data import FixedPointingInfo, Observation, observatory_locations
from gammapy.datasets import SpectrumDataset, SpectrumDatasetOnOff
from gammapy.estimators import SensitivityEstimator
from gammapy.makers import SpectrumDatasetMaker
from gammapy.maps import MapAxis, RegionGeom
from regions import CircleSkyRegion

from .config import SensitivityCriteria

DEFAULT_OFFSET = 0.5 * u.deg


def log_energy_axis(lo_exp=-1.9, hi_exp=2.3, per_decade=5, name="energy"):
    """Energy axis with edges at 10**(lo_exp + k/per_decade) TeV."""
    n = int(round((hi_exp - lo_exp) * per_decade))
    edges = np.logspace(lo_exp, hi_exp, n + 1) * u.TeV
    return MapAxis.from_energy_edges(edges, name=name)


def single_bin_axis(energy, half_width_dex=0.1):
    """One reconstructed-energy bin of 2 * half_width_dex decades centred on energy."""
    energy = u.Quantity(energy, "TeV")
    edges = u.Quantity([energy * 10**-half_width_dex, energy * 10**half_width_dex])
    return MapAxis.from_energy_edges(edges, name="energy")


TRUE_ENERGY_AXIS = MapAxis.from_energy_bounds(
    0.005 * u.TeV, 500 * u.TeV, nbin=25, per_decade=True, name="energy_true"
)


def sensitivity(
    irfs,
    livetime,
    location="ctao_south",
    energy_axis=None,
    offset=DEFAULT_OFFSET,
    criteria: SensitivityCriteria | None = None,
):
    """Differential point-source sensitivity in E^2 dN/dE (erg cm-2 s-1).

    The on region is the ``criteria.containment`` PSF containment radius in
    each energy bin. Returns ``(energy_axis, e2dnde, table)``; bins where the
    sensitivity cannot be computed are NaN.
    """
    criteria = criteria or SensitivityCriteria()
    energy_axis = energy_axis or log_energy_axis()
    livetime = u.Quantity(livetime, "s")
    pointing = SkyCoord(0, 0, unit="deg", frame="icrs")
    source = pointing.directional_offset_by(0 * u.deg, offset)
    ref_radius = 0.1 * u.deg

    geom = RegionGeom.create(CircleSkyRegion(source, ref_radius), axes=[energy_axis])
    empty = SpectrumDataset.create(geom=geom, energy_axis_true=TRUE_ENERGY_AXIS)
    obs = Observation.create(
        pointing=FixedPointingInfo(fixed_icrs=pointing),
        irfs=irfs,
        livetime=livetime,
        location=observatory_locations[location],
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        maker = SpectrumDatasetMaker(selection=["exposure", "edisp", "background"])
        dataset = maker.run(empty, obs)

        dataset.exposure *= criteria.containment
        radii = obs.psf.containment_radius(
            energy_true=energy_axis.center, offset=offset, fraction=criteria.containment
        )
        factor = (1 - np.cos(radii)) / (1 - np.cos(ref_radius))
        dataset.background *= factor.value.reshape((-1, 1, 1))

        on_off = SpectrumDatasetOnOff.from_spectrum_dataset(
            dataset=dataset, acceptance=1, acceptance_off=1 / criteria.alpha
        )
        estimator = SensitivityEstimator(
            n_sigma=criteria.n_sigma,
            gamma_min=criteria.gamma_min,
            bkg_syst_fraction=criteria.bkg_syst_fraction,
        )
        table = estimator.run(on_off)
    e2dnde = np.array(table["e2dnde"].quantity.to_value("erg cm-2 s-1"), dtype=float)
    e2dnde[~np.isfinite(e2dnde) | (e2dnde <= 0)] = np.nan
    return energy_axis, e2dnde, table


def angular_resolution(irfs, energy, offset=DEFAULT_OFFSET, fraction=0.68):
    """PSF containment radius (deg) at the given true energies."""
    radius = irfs["psf"].containment_radius(
        energy_true=u.Quantity(energy, "TeV"), offset=offset, fraction=fraction
    )
    radius = radius.to_value("deg")
    return np.where(radius > 0, radius, np.nan)


def _migration_weights(irfs, offset, index, migra):
    edisp, aeff = irfs["edisp"], irfs["aeff"]
    et_axis = edisp.axes["energy_true"]
    et = et_axis.center
    pdf = edisp.evaluate(energy_true=et[:, None], migra=migra[None, :], offset=offset).value
    norm = pdf.sum(axis=1, keepdims=True)
    pdf = np.divide(pdf, norm, out=np.zeros_like(pdf), where=norm > 0)
    w = aeff.evaluate(energy_true=et, offset=offset).to_value("m2")
    w = w * et.to_value("TeV") ** -index * et_axis.bin_width.to_value("TeV")
    return et.to_value("TeV"), pdf * w[:, None]


def _half_width(dist, weights, fraction):
    order = np.argsort(dist)
    cum = np.cumsum(weights[order])
    if cum[-1] <= 0:
        return np.nan
    return np.interp(fraction * cum[-1], cum, dist[order])


def energy_resolution(
    irfs, energy_edges, axis="reco_energy", offset=DEFAULT_OFFSET, index=2.62, fraction=0.68
):
    """Half-width of the interval around 0 containing ``fraction`` of (E_R - E_T)/E_T.

    ``axis`` selects whether ``energy_edges`` bin reconstructed or true energy.
    True energies are weighted with A_eff(E_T) * E_T**-index.
    """
    edges = u.Quantity(energy_edges, "TeV").value
    migra = np.linspace(0.2, 2.0, 1801)  # oversample the 0.01-wide migration bins
    et, weights = _migration_weights(irfs, offset, index, migra)
    dist = np.broadcast_to(np.abs(migra - 1)[None, :], weights.shape)
    if axis == "reco_energy":
        energy = et[:, None] * migra[None, :]
    elif axis == "true_energy":
        energy = np.broadcast_to(et[:, None], weights.shape)
    else:
        raise ValueError(f"axis must be 'reco_energy' or 'true_energy', got {axis!r}")

    res = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (energy >= lo) & (energy < hi) & (weights > 0)
        res.append(_half_width(dist[sel], weights[sel], fraction) if sel.any() else np.nan)
    return np.array(res)


def effective_area(irfs, offset=DEFAULT_OFFSET):
    """Effective area (m2) on the native true-energy binning of the IRF."""
    aeff = irfs["aeff"]
    axis = aeff.axes["energy_true"]
    values = aeff.evaluate(energy_true=axis.center, offset=offset).to_value("m2")
    return axis, values


def background_rate(irfs, offset=DEFAULT_OFFSET):
    """Residual background rate (Hz/deg2) integrated in the native reco-energy bins."""
    bkg = irfs["bkg"]
    axis = bkg.axes["energy"]
    rate = bkg.evaluate(energy=axis.center, fov_lon=u.Quantity(offset), fov_lat=0 * u.deg)
    return axis, (rate * axis.bin_width).to_value("s-1 deg-2")
