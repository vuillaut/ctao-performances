"""Figure registry.

A *producer* is a function taking a :class:`Context` and yielding
:class:`FigureResult` objects. Register new figures with ``@producer``; they
are then generated for every release.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
from gammapy.maps import MapAxis
from matplotlib.figure import Figure

from . import performance as perf
from .config import Release
from .irfs import IRFLibrary
from .plotting import (
    COLORS,
    E_RECO_LABEL,
    E_TRUE_LABEL,
    LINESTYLES,
    SENS_LABEL,
    binned_points,
    finish,
    new_figure,
)

log = logging.getLogger(__name__)

PRODUCERS = []


def producer(func):
    PRODUCERS.append(func)
    return func


@dataclass
class FigureResult:
    id: str
    title: str
    caption: str
    figure: Figure


class Context:
    """A release, its IRFs and a cache of computed sensitivities."""

    def __init__(self, release: Release, data_dir):
        self.release = release
        self.irfs = IRFLibrary(release, data_dir)
        self._cache = {}

    @property
    def sites(self):
        return list(self.release.sites.values())

    @property
    def offset(self):
        return self.release.offset

    def load(self, site, duration=None, **selection):
        return self.irfs.load(site, duration or self.release.reference_duration, **selection)

    def sensitivity(self, site, duration=None, livetime=None, offset=None, energy_axis=None,
                    **selection):
        """Sensitivity of one site; ``livetime`` defaults to the optimisation time."""
        duration = duration or self.release.reference_duration
        livetime = u.Quantity(livetime if livetime is not None else duration, "s")
        offset = self.offset if offset is None else offset
        key = (site, duration, livetime.value, u.Quantity(offset).to_value("deg"),
               None if energy_axis is None else tuple(energy_axis.edges.value),
               tuple(sorted(selection.items())))
        if key not in self._cache:
            axis, e2, _ = perf.sensitivity(
                self.load(site, duration, **selection),
                livetime=livetime,
                location=self.release.sites[site].location,
                energy_axis=energy_axis,
                offset=offset,
                criteria=self.release.sensitivity,
            )
            self._cache[key] = (axis, e2)
        return self._cache[key]

    def mask_below_threshold(self, site, edges, values):
        """NaN for bins below the lowest energy shown in the official figures."""
        values = np.array(values, dtype=float)
        e_min = self.release.sites[site].e_min.to_value("TeV")
        values[np.asarray(u.Quantity(edges, "TeV").value)[:-1] < e_min * 0.99] = np.nan
        return values


def _sens_axes(ylim=(2e-14, 3e-10)):
    fig, ax = new_figure()
    ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=ylim,
           xlabel=E_RECO_LABEL, ylabel=SENS_LABEL)
    return fig, ax


def _ref_label(release):
    return release.duration_label(release.reference_duration)


# --------------------------------------------------------------------------
# Sensitivity
# --------------------------------------------------------------------------
@producer
def sensitivity_durations(ctx: Context):
    rel = ctx.release
    for site in ctx.sites:
        fig, ax = _sens_axes(ylim=(2e-14, 3e-8))
        for i, (label, duration) in enumerate(rel.durations.items()):
            if not ctx.irfs.exists(site.key, duration):
                continue
            axis, e2 = ctx.sensitivity(site.key, duration)
            e2 = ctx.mask_below_threshold(site.key, axis.edges, e2)
            binned_points(ax, axis.edges.to_value("TeV"), e2, i, f"{site.label} ({label})")
        ax.legend(loc="upper center", ncols=2, fontsize=11)
        ax.text(0.04, 0.04, "Differential flux sensitivity", transform=ax.transAxes)
        yield FigureResult(
            f"sensitivity-durations-{site.key}",
            f"{site.label}: differential sensitivity vs observation time",
            "Point-source differential sensitivity (5σ, ≥10 excess events, S/B ≥ 5%, "
            "5 bins per decade) for each observation time, using the IRFs optimised "
            f"for that time. Zenith {rel.zenith}°, {rel.azimuth}, offset {ctx.offset}.",
            finish(fig, ax, rel),
        )


@producer
def sensitivity_north_south(ctx: Context):
    rel = ctx.release
    fig, ax = _sens_axes()
    for i, site in enumerate(ctx.sites):
        axis, e2 = ctx.sensitivity(site.key)
        e2 = ctx.mask_below_threshold(site.key, axis.edges, e2)
        binned_points(ax, axis.edges.to_value("TeV"), e2, i, site.label)
    ax.legend(loc="upper center", fontsize=14)
    ax.text(0.04, 0.04, f"Differential flux sensitivity ({_ref_label(rel)})",
            transform=ax.transAxes)
    yield FigureResult(
        "sensitivity-north-south",
        f"Differential sensitivity, North vs South ({_ref_label(rel)})",
        f"Point-source differential sensitivity of both arrays for {_ref_label(rel)} of "
        f"observation. Zenith {rel.zenith}°, {rel.azimuth}.",
        finish(fig, ax, rel),
    )


@producer
def sensitivity_zenith(ctx: Context):
    rel = ctx.release
    for site in ctx.sites:
        fig, ax = _sens_axes()
        n = 0
        for i, zenith in enumerate(rel.zeniths):
            if not ctx.irfs.exists(site.key, rel.reference_duration, zenith=zenith):
                continue
            axis, e2 = ctx.sensitivity(site.key, zenith=zenith)
            e2 = ctx.mask_below_threshold(site.key, axis.edges, e2)
            binned_points(ax, axis.edges.to_value("TeV"), e2, i, f"zenith {zenith}°")
            n += 1
        if n < 2:
            plt.close(fig)
            continue
        ax.legend(loc="upper center", title=site.label)
        yield FigureResult(
            f"sensitivity-zenith-{site.key}",
            f"{site.label}: differential sensitivity vs zenith angle",
            f"Differential sensitivity ({_ref_label(rel)}) for the available zenith angles. "
            "The energy threshold rises with zenith angle while the high-energy "
            "sensitivity improves thanks to the larger light pool.",
            finish(fig, ax, rel),
        )


@producer
def sensitivity_validation(ctx: Context):
    """Compare our sensitivity with the one tabulated in the FITS files (if any)."""
    rel = ctx.release
    for site in ctx.sites:
        provided = ctx.irfs.provided_sensitivity(site.key, rel.reference_duration)
        if provided is None:
            continue
        e_edges, t_edges, table = provided
        theta = 0.5 * (t_edges[:-1] + t_edges[1:])
        j = int(np.argmin(np.abs(theta - ctx.offset)))
        axis = MapAxis.from_energy_edges(e_edges, name="energy")
        _, ours = ctx.sensitivity(site.key, energy_axis=axis)
        ours = ctx.mask_below_threshold(site.key, e_edges, ours)
        theirs = ctx.mask_below_threshold(site.key, e_edges, table[j])

        fig = plt.figure(figsize=(8, 6.4))
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.05)
        ax, axr = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
        edges = e_edges.to_value("TeV")
        binned_points(ax, edges, theirs, 1, "tabulated in the FITS file (official)")
        binned_points(ax, edges, ours, 0, "computed with gammapy from the IRFs", open_marker=True)
        ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=(2e-14, 3e-10), ylabel=SENS_LABEL)
        ax.tick_params(labelbottom=False)
        ax.legend(loc="upper center", title=f"{site.label} ({_ref_label(rel)})")
        binned_points(axr, edges, ours / theirs, 0)
        axr.axhline(1, color="#888888", ls="--", lw=1)
        axr.set(xscale="log", xlim=(1e-2, 300), ylim=(0.3, 3), yscale="log",
                xlabel=E_RECO_LABEL, ylabel="gammapy / official")
        for a in (ax, axr):
            a.tick_params(which="both", direction="in", top=True, right=True)
        fig.subplots_adjust(left=0.12, right=0.93, top=0.97, bottom=0.1)
        ax.text(1.015, 0.2, f"doi:{rel.doi} ({rel.name})", transform=ax.transAxes,
                rotation=90, fontsize=7, color="#555555")
        yield FigureResult(
            f"sensitivity-validation-{site.key}",
            f"{site.label}: gammapy sensitivity vs official tabulated sensitivity",
            "Validation: the release ships the official differential sensitivity in a "
            "DIFFERENTIAL SENSITIVITY HDU. It is compared with the sensitivity that "
            "gammapy derives from the effective area, PSF, energy dispersion and "
            "background of the same file.",
            fig,
        )


@producer
def offaxis_sensitivity(ctx: Context):
    rel = ctx.release
    bins = rel.offaxis.get("bins_tev", [])
    if not bins:
        return
    offsets = np.arange(0.5, 4.51, 0.25) * u.deg
    for site in ctx.sites:
        fig, ax = new_figure((6.5, 6))
        curves = []
        for off in offsets:
            axis, e2 = ctx.sensitivity(site.key, offset=off)
            curves.append(e2)
        curves = np.array(curves)
        centers = axis.center.to_value("TeV")
        for i, (lo, hi) in enumerate(bins):
            j = int(np.argmin(np.abs(np.log(centers / np.sqrt(lo * hi)))))
            rel_curve = curves[:, j] / curves[0, j]
            label = f"{lo * 1e3:g} - {hi * 1e3:g} GeV" if hi < 1 else f"{lo:g} - {hi:g} TeV"
            ax.plot(offsets, rel_curve, color=COLORS[i], ls=LINESTYLES[i], lw=2.5, label=label)
        ax.axhline(1, color="#999999", ls="--", lw=1)
        ax.set(yscale="log", xlim=(0, 4.5), ylim=(0.6, 6),
               xlabel="Angle w.r.t. the FoV center [deg]",
               ylabel="Point-source flux sensitivity relative to FoV center")
        ax.legend(loc="upper left", title=site.label)
        yield FigureResult(
            f"offaxis-sensitivity-{site.key}",
            f"{site.label}: off-axis sensitivity",
            f"Differential sensitivity ({_ref_label(rel)}) at increasing distance from the "
            "centre of the field of view, relative to the value at 0.5°. The IRFs have "
            "1°-wide offset bins and gammapy interpolates linearly between them.",
            finish(fig, ax, rel),
        )


@producer
def sensitivity_vs_time(ctx: Context):
    rel = ctx.release
    cfg = rel.short_term
    if not cfg:
        return
    duration = cfg["duration"]
    times = np.geomspace(10, 1e4, 25) * u.s
    styles = ["-", "--", ":", "-.", (0, (3, 1, 1, 1, 1, 1))]
    for site in ctx.sites:
        if not ctx.irfs.exists(site.key, duration):
            continue
        fig, ax = new_figure()
        for i, e_gev in enumerate(cfg["energies_gev"]):
            axis = perf.single_bin_axis(e_gev * 1e-3 * u.TeV)
            if axis.edges[0] < site.e_min * 0.99:
                continue
            values = [ctx.sensitivity(site.key, duration, livetime=t, energy_axis=axis)[1][0]
                      for t in times]
            ax.plot(times, values, color=COLORS[0], ls=styles[i % len(styles)], lw=2.2,
                    label=f"E = {e_gev:g} GeV")
        for t, lab in [(60, "1 min"), (600, "10 min"), (3600, "1 hour")]:
            ax.axvline(t, color="#bbbbbb", lw=0.8, zorder=0)
            ax.text(t, 1.5e-13, lab, ha="center", fontsize=10, color="#555555",
                    bbox=dict(fc="white", ec="none", pad=1))
        ax.set(xscale="log", yscale="log", xlim=(10, 1e4), ylim=(1e-13, 3e-9), xlabel="Time [s]",
               ylabel=r"Differential flux sensitivity E$^2$dN/dE [erg cm$^{-2}$ s$^{-1}$]")
        ax.legend(loc="upper right", title=f"{site.label} ({rel.configuration})")
        yield FigureResult(
            f"sensitivity-time-{site.key}",
            f"{site.label}: sensitivity vs observation time",
            "Differential sensitivity in 0.2-decade bins centred on selected energies as a "
            f"function of observation time, using the IRFs optimised for "
            f"{rel.duration_label(duration)}.",
            finish(fig, ax, rel),
        )


# --------------------------------------------------------------------------
# Instrument response
# --------------------------------------------------------------------------
@producer
def angular_resolution(ctx: Context):
    rel = ctx.release
    fig, ax = new_figure((7, 5.5))
    for i, site in enumerate(ctx.sites):
        energy = np.geomspace(site.e_min.to_value("TeV"), 200, 200) * u.TeV
        r68 = perf.angular_resolution(ctx.load(site.key), energy, offset=ctx.offset)
        ax.plot(energy, r68, color=COLORS[i], ls=LINESTYLES[i], lw=2.5, label=site.label)
    ax.set(xscale="log", xlim=(1e-2, 300), ylim=(0, 0.25), xlabel=E_TRUE_LABEL,
           ylabel="Angular resolution (68% containment) [deg]")
    ax.legend(loc="upper right", fontsize=14)
    yield FigureResult(
        "angular-resolution",
        f"Angular resolution ({_ref_label(rel)})",
        "68% containment radius of the triple-Gaussian PSF of the FITS IRFs. The official curves use the "
        "full point-spread distribution from the ROOT files.",
        finish(fig, ax, rel),
    )


@producer
def energy_resolution(ctx: Context):
    rel = ctx.release
    axis_type = rel.energy_resolution_axis
    edges = perf.log_energy_axis().edges
    fig, ax = new_figure((7, 5.5))
    for i, site in enumerate(ctx.sites):
        res = perf.energy_resolution(ctx.load(site.key), edges, axis=axis_type, offset=ctx.offset)
        res = ctx.mask_below_threshold(site.key, edges, res)
        binned_points(ax, edges.to_value("TeV"), res, i, site.label)
    ax.set(xscale="log", xlim=(1e-2, 300), ylim=(0, 0.3),
           xlabel=E_RECO_LABEL if axis_type == "reco_energy" else E_TRUE_LABEL,
           ylabel=r"$\Delta E / E$ (68% containment)")
    ax.legend(loc="upper right", fontsize=14)
    yield FigureResult(
        "energy-resolution",
        f"Energy resolution ({_ref_label(rel)})",
        "Half-width of the interval around 0 containing 68% of (E_R − E_T)/E_T, from the "
        "energy-dispersion matrix weighted by the effective area and an E^-2.62 spectrum, "
        f"in bins of {'reconstructed' if axis_type == 'reco_energy' else 'true'} energy.",
        finish(fig, ax, rel),
    )


@producer
def effective_area(ctx: Context):
    rel = ctx.release
    for site in ctx.sites:
        fig, ax = new_figure((7, 5.5))
        for i, (label, duration) in enumerate(rel.durations.items()):
            if not ctx.irfs.exists(site.key, duration):
                continue
            axis, aeff = perf.effective_area(ctx.load(site.key, duration), offset=ctx.offset)
            aeff = np.where(aeff > 0, aeff, np.nan)
            ax.plot(axis.center, aeff, color=COLORS[i], ls=LINESTYLES[i], lw=2.5,
                    label=f"{site.label} ({label})")
        ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=(1e2, 1e7),
               xlabel=E_TRUE_LABEL, ylabel=r"Effective area [m$^2$]")
        ax.legend(loc="lower right")
        ax.text(0.04, 0.93, "After gamma/hadron separation cuts", transform=ax.transAxes)
        yield FigureResult(
            f"effective-area-{site.key}",
            f"{site.label}: effective area",
            "Effective collection area after gamma/hadron separation, without cut on the "
            "reconstructed direction (the FITS IRFs are full-enclosure), for each "
            "observation-time optimisation.",
            finish(fig, ax, rel),
        )


@producer
def background_rate(ctx: Context):
    rel = ctx.release
    fig, ax = new_figure((7, 5.5))
    for i, site in enumerate(ctx.sites):
        axis, rate = perf.background_rate(ctx.load(site.key), offset=ctx.offset)
        rate = np.where(rate > 0, rate, np.nan)
        rate = ctx.mask_below_threshold(site.key, axis.edges, rate)
        binned_points(ax, axis.edges.to_value("TeV"), rate, i, site.label)
    ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=(1e-5, 10),
           xlabel=E_RECO_LABEL, ylabel=r"Background rate [Hz deg$^{-2}$]")
    ax.legend(loc="upper right", fontsize=14)
    yield FigureResult(
        "background-rate",
        f"Residual background rate ({_ref_label(rel)})",
        "Post-analysis cosmic-ray background rate per square degree near the centre of the "
        "field of view, integrated in 0.2-decade bins of reconstructed energy.",
        finish(fig, ax, rel),
    )


# --------------------------------------------------------------------------
def make_figures(release: Release, data_dir, out_dir, only=None) -> list[dict]:
    """Run every producer and save PNGs to ``out_dir``. Returns a manifest."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = Context(release, data_dir)
    manifest = []
    for prod in PRODUCERS:
        if only and prod.__name__ not in only:
            continue
        try:
            for result in prod(ctx):
                path = out_dir / f"{result.id}.png"
                result.figure.savefig(path)
                plt.close(result.figure)
                log.info("%s: wrote %s", release.name, path.name)
                manifest.append({
                    "id": result.id,
                    "title": result.title,
                    "caption": result.caption,
                    "file": path.name,
                    "reference": release.reference_figures.get(result.id),
                })
        except FileNotFoundError as exc:
            log.warning("%s: skipping %s (%s)", release.name, prod.__name__, exc)
    return manifest
