"""Figure registry.

A *producer* is a function taking a :class:`Context` and yielding :class:`FigureResult`
objects. Register new figures with ``@producer``; they are then generated for every release
and for every source they support:

* ``gammapy``: numbers recomputed with gammapy from the FITS IRFs;
* ``root``: official curves read from the ROOT files.

Both are drawn by the same code, from :class:`~ctao_perf.curves.Curve` objects. Each figure is
saved as a PNG together with an ASCII file of the plotted points and a Python snippet that
plots that file again.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from .ascii import ascii_table, plot_snippet
from .config import Release
from .curves import Curve
from .plotting import (
    COLORS,
    E_RECO_LABEL,
    E_TRUE_LABEL,
    LINESTYLES,
    SENS_LABEL,
    apply_style,
    draw_curve,
    finish,
    new_figure,
)
from .sources import SOURCES, GammapySource, RootSource

log = logging.getLogger(__name__)

PRODUCERS = []
ALL_SOURCES = ("gammapy", "root")


def producer(func=None, *, sources=ALL_SOURCES):
    """Register a figure producer, for the given sources (default: both)."""

    def register(f):
        f.sources = tuple(sources)
        PRODUCERS.append(f)
        return f

    return register(func) if func is not None else register


@dataclass
class FigureResult:
    id: str
    title: str
    caption: str
    figure: Figure
    curves: list[Curve] = field(default_factory=list)
    xlabel: str = ""
    ylabel: str = ""
    xscale: str = "log"
    yscale: str = "log"
    hline: float | None = None  # horizontal reference line drawn by the snippet


class Context:
    """A release, its data sources, and the one the figures are being drawn from."""

    def __init__(self, release: Release, data_dir, source="gammapy"):
        self.release = release
        self.data_dir = data_dir
        self.gammapy = GammapySource(release, data_dir)
        self.root = RootSource(release, data_dir)
        self.source = source

    @property
    def src(self):
        return self.gammapy if self.source == "gammapy" else self.root

    @property
    def sites(self):
        return list(self.release.sites.values())

    @property
    def offset(self):
        return self.release.offset

    def caption(self, gammapy, root):
        return gammapy if self.source == "gammapy" else root

    def mask(self, site, curve: Curve) -> Curve:
        """NaN for bins below the lowest energy shown in the official figures."""
        e_min = self.release.sites[site].e_min.to_value("TeV")
        return curve.masked(curve.xlo < e_min * 0.99) if curve.is_binned else curve

    def finish(self, fig, ax):
        return finish(fig, ax, self.release, self.source)


def _sens_axes(ylim=(2e-14, 3e-10)):
    fig, ax = new_figure()
    ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=ylim,
           xlabel=E_RECO_LABEL, ylabel=SENS_LABEL)
    return fig, ax


def _ref_label(release):
    return release.duration_label(release.reference_duration)


_SENS_LABEL_TXT = "E^2 x flux sensitivity [erg cm-2 s-1]"
_CRITERIA = "5σ, ≥10 excess events, S/B ≥ 5%, 5 bins per decade"


# --------------------------------------------------------------------------
# Sensitivity
# --------------------------------------------------------------------------
@producer
def sensitivity_durations(ctx: Context):
    rel = ctx.release
    for site in ctx.sites:
        fig, ax = _sens_axes(ylim=(2e-14, 3e-8))
        curves = []
        for i, (label, duration) in enumerate(rel.durations.items()):
            if not ctx.src.exists(site.key, duration):
                continue
            curve = ctx.mask(site.key, ctx.src.sensitivity(site.key, duration))
            curve = curve.with_label(f"{site.label} ({label})")
            draw_curve(ax, curve, i)
            curves.append(curve)
        if not curves:
            plt.close(fig)
            continue
        ax.legend(loc="upper center", ncols=2, fontsize=11)
        ax.text(0.04, 0.04, "Differential flux sensitivity", transform=ax.transAxes)
        yield FigureResult(
            f"sensitivity-durations-{site.key}",
            f"{site.label}: differential sensitivity vs observation time",
            ctx.caption(
                f"Point-source differential sensitivity ({_CRITERIA}) computed with gammapy "
                "for each observation time, using the IRFs optimised for that time. "
                f"Zenith {rel.zenith}°, {rel.azimuth}, offset {ctx.offset}.",
                "Official differential sensitivity (histogram DiffSens of the ROOT files) for "
                f"each observation time. Zenith {rel.zenith}°, {rel.azimuth}.",
            ),
            ctx.finish(fig, ax), curves,
            "Reconstructed gamma-ray energy E_R [TeV]", _SENS_LABEL_TXT,
        )


@producer
def sensitivity_north_south(ctx: Context):
    rel = ctx.release
    fig, ax = _sens_axes()
    curves = []
    for i, site in enumerate(ctx.sites):
        if not ctx.src.exists(site.key):
            continue
        curve = ctx.mask(site.key, ctx.src.sensitivity(site.key)).with_label(site.label)
        draw_curve(ax, curve, i)
        curves.append(curve)
    if not curves:
        plt.close(fig)
        return
    ax.legend(loc="upper center", fontsize=14)
    ax.text(0.04, 0.04, f"Differential flux sensitivity ({_ref_label(rel)})", transform=ax.transAxes)
    yield FigureResult(
        "sensitivity-north-south",
        f"Differential sensitivity, North vs South ({_ref_label(rel)})",
        ctx.caption(
            f"Point-source differential sensitivity of both arrays for {_ref_label(rel)} of "
            f"observation, computed with gammapy. Zenith {rel.zenith}°, {rel.azimuth}.",
            f"Official differential sensitivity of both arrays for {_ref_label(rel)} of "
            f"observation (DiffSens). Zenith {rel.zenith}°, {rel.azimuth}.",
        ),
        ctx.finish(fig, ax), curves,
        "Reconstructed gamma-ray energy E_R [TeV]", _SENS_LABEL_TXT,
    )


@producer
def sensitivity_zenith(ctx: Context):
    rel = ctx.release
    for site in ctx.sites:
        fig, ax = _sens_axes()
        curves = []
        for i, zenith in enumerate(rel.zeniths):
            if not ctx.src.exists(site.key, rel.reference_duration, zenith=zenith):
                continue
            curve = ctx.src.sensitivity(site.key, zenith=zenith)
            curve = ctx.mask(site.key, curve).with_label(f"zenith {zenith}°")
            draw_curve(ax, curve, i)
            curves.append(curve)
        if len(curves) < 2:
            plt.close(fig)
            continue
        ax.legend(loc="upper center", title=site.label)
        yield FigureResult(
            f"sensitivity-zenith-{site.key}",
            f"{site.label}: differential sensitivity vs zenith angle",
            f"Differential sensitivity ({_ref_label(rel)}) for the available zenith angles"
            + ctx.caption(", computed with gammapy", " (official, from the ROOT files)")
            + ". The energy threshold rises with zenith angle while the high-energy "
            "sensitivity improves thanks to the larger light pool.",
            ctx.finish(fig, ax), curves,
            "Reconstructed gamma-ray energy E_R [TeV]", _SENS_LABEL_TXT,
        )


def _official_at_offset(ctx: Context, site):
    """Official sensitivity in the offset bin of the source, the one the FITS IRFs describe.

    ``(label, Curve)`` from ``DiffSens_offaxis`` in the ROOT file, or from the
    ``DIFFERENTIAL SENSITIVITY`` HDU of the FITS file (same values) when the ROOT file is missing.
    """
    if ctx.root.available() and ctx.root.exists(site.key):
        curve, (lo, hi) = ctx.root.sensitivity_at_offset(site.key, ctx.offset)
        return f"official, {lo:g}–{hi:g}° off axis (ROOT file)", curve
    provided = ctx.gammapy.irfs.provided_sensitivity(site.key, ctx.release.reference_duration)
    if provided is None:
        return None
    e_edges, t_edges, table = provided
    t_edges, offset = t_edges.to_value("deg"), ctx.offset.to_value("deg")
    j = int(np.clip(np.searchsorted(t_edges, offset, side="right") - 1, 0, len(t_edges) - 2))
    label = f"official, {t_edges[j]:g}–{t_edges[j + 1]:g}° off axis (FITS file)"
    return label, Curve.binned(e_edges.to_value("TeV"), table[j])


def _official_on_axis(ctx: Context, site):
    """``DiffSens`` of the ROOT file: the official curve, for a source on the camera axis."""
    if ctx.root.available() and ctx.root.exists(site.key):
        return "official, on axis (ROOT file)", ctx.root.sensitivity(site.key)
    return None


def _validation(ctx: Context, site, ours, official, suffix, where, why):
    """The gammapy sensitivity next to one official sensitivity, and their ratio."""
    rel = ctx.release
    label, official = official
    official = ctx.mask(site.key, official).with_label(label)
    fig, ax = _sens_axes()
    draw_curve(ax, official, 1)
    draw_curve(ax, ours, 0, open_marker=True)
    ax.legend(loc="upper center", title=f"{site.label} ({_ref_label(rel)})")
    yield FigureResult(
        f"sensitivity-validation{suffix}-{site.key}",
        f"{site.label}: gammapy sensitivity vs official sensitivity, {where}",
        "Validation: the sensitivity computed with gammapy from the effective area, PSF, "
        f"energy dispersion and background of the FITS file, next to the official one {where}. "
        + why + " See the documentation for why they differ.",
        ctx.finish(fig, ax), [official, ours],
        "Reconstructed gamma-ray energy E_R [TeV]", _SENS_LABEL_TXT,
    )

    if not (official.is_binned and len(official.y) == len(ours.y)
            and np.allclose(official.xlo, ours.xlo, rtol=1e-3)
            and np.allclose(official.xhi, ours.xhi, rtol=1e-3)):
        log.warning("%s: no ratio to %s, its energy bins differ from ours", site.key, label)
        return
    ratio = Curve(ours.x, ours.y / official.y, ours.xlo, ours.xhi, f"gammapy / {label}").positive()
    fig, ax = new_figure((8, 4))
    draw_curve(ax, ratio, 1)
    ax.axhline(1, color="#888888", ls="--", lw=1)
    ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=(0.3, 3),
           xlabel=E_RECO_LABEL, ylabel="gammapy / official")
    ax.legend(loc="upper center", title=f"{site.label} ({_ref_label(rel)})")
    yield FigureResult(
        f"sensitivity-ratio{suffix}-{site.key}",
        f"{site.label}: ratio of the gammapy sensitivity to the official one, {where}",
        f"The gammapy sensitivity divided by the official sensitivity {where}, bin by bin. "
        "A ratio above 1 means the gammapy sensitivity is worse (a larger flux is needed).",
        ctx.finish(fig, ax), [ratio],
        "Reconstructed gamma-ray energy E_R [TeV]", "gammapy / official", hline=1.0,
    )


@producer(sources=("gammapy",))
def sensitivity_validation(ctx: Context):
    """The gammapy sensitivity next to the official one, for the source offset bin and on axis."""
    for site in ctx.sites:
        if not ctx.gammapy.exists(site.key):
            continue
        ours = ctx.mask(site.key, ctx.gammapy.sensitivity(site.key)).with_label("computed with gammapy")
        official = _official_at_offset(ctx, site)
        if official is not None:
            yield from _validation(
                ctx, site, ours, official, "", "for the same source offset",
                "The FITS IRFs describe a source in this 1° offset bin, so this is the official "
                "curve the gammapy calculation can be compared with.",
            )
        official = _official_on_axis(ctx, site)
        if official is not None:
            yield from _validation(
                ctx, site, ours, official, "-onaxis", "on the camera axis",
                "This is the curve of the official CTAO figures. It is for a source on the camera "
                "axis, while the FITS IRFs are for a source 0–1° off axis, where the sensitivity is "
                "a few percent worse.",
            )


@producer
def offaxis_sensitivity(ctx: Context):
    rel = ctx.release
    bins = rel.offaxis.get("bins_tev", [])
    if not bins:
        return
    for site in ctx.sites:
        if not ctx.src.exists(site.key):
            continue
        offsets, centers, curves = ctx.src.sensitivity_offaxis(site.key)
        fig, ax = new_figure((6.5, 6))
        out = []
        for i, (lo, hi) in enumerate(bins):
            j = int(np.argmin(np.abs(np.log(centers / np.sqrt(lo * hi)))))
            label = f"{lo * 1e3:g} - {hi * 1e3:g} GeV" if hi < 1 else f"{lo:g} - {hi:g} TeV"
            curve = Curve(offsets, curves[:, j] / curves[0, j], label=label)
            draw_curve(ax, curve, i, ls=LINESTYLES[i])
            out.append(curve)
        ax.axhline(1, color="#999999", ls="--", lw=1)
        ax.set(yscale="log", xlim=(0, 4.5), ylim=(0.6, 6),
               xlabel="Angle w.r.t. the FoV center [deg]",
               ylabel="Point-source flux sensitivity relative to FoV center")
        ax.legend(loc="upper left", title=site.label)
        yield FigureResult(
            f"offaxis-sensitivity-{site.key}",
            f"{site.label}: off-axis sensitivity",
            ctx.caption(
                f"Differential sensitivity ({_ref_label(rel)}) computed with gammapy at increasing "
                f"distance from the centre of the field of view, relative to the value at "
                f"{offsets[0]:g}°. The IRFs have 1°-wide offset bins and gammapy interpolates "
                "linearly between their centres.",
                f"Official differential sensitivity ({_ref_label(rel)}) per 1°-wide offset bin "
                f"(DiffSens_offaxis), relative to the first bin ({offsets[0]:g}°). Only the bins "
                "with a value are shown.",
            ),
            ctx.finish(fig, ax), out,
            "Angle w.r.t. the FoV center [deg]", "Sensitivity relative to the FoV center",
            xscale="linear",
        )


@producer(sources=("gammapy",))
def sensitivity_vs_time(ctx: Context):
    from . import performance as perf

    rel = ctx.release
    cfg = rel.short_term
    if not cfg:
        return
    duration = cfg["duration"]
    times = np.geomspace(10, 1e4, 25)
    styles = ["-", "--", ":", "-.", (0, (3, 1, 1, 1, 1, 1))]
    for site in ctx.sites:
        if not ctx.gammapy.exists(site.key, duration):
            continue
        fig, ax = new_figure()
        curves = []
        for i, e_gev in enumerate(cfg["energies_gev"]):
            axis = perf.single_bin_axis(e_gev * 1e-3 * u.TeV)
            if axis.edges[0] < site.e_min * 0.99:
                continue
            values = [ctx.gammapy.sensitivity(site.key, duration, livetime=t * u.s, energy_axis=axis).y[0]
                      for t in times]
            curve = Curve(times, values, label=f"E = {e_gev:g} GeV")
            draw_curve(ax, curve, 0, ls=styles[i % len(styles)])
            curves.append(curve)
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
            f"function of observation time, computed with gammapy using the IRFs optimised for "
            f"{rel.duration_label(duration)}. There is no equivalent curve in the ROOT files.",
            ctx.finish(fig, ax), curves, "Time [s]", "E^2 dN/dE sensitivity [erg cm-2 s-1]",
        )


# --------------------------------------------------------------------------
# Instrument response
# --------------------------------------------------------------------------
@producer
def angular_resolution(ctx: Context):
    rel = ctx.release
    fig, ax = new_figure((7, 5.5))
    curves = []
    for i, site in enumerate(ctx.sites):
        if not ctx.src.exists(site.key):
            continue
        curve = ctx.src.angular_resolution(site.key).with_label(site.label)
        draw_curve(ax, curve, i)
        curves.append(curve)
    if not curves:
        plt.close(fig)
        return
    ax.set(xscale="log", xlim=(1e-2, 300), ylim=(0, 0.25), xlabel=E_TRUE_LABEL,
           ylabel="Angular resolution (68% containment) [deg]")
    ax.legend(loc="upper right", fontsize=14)
    yield FigureResult(
        "angular-resolution",
        f"Angular resolution ({_ref_label(rel)})",
        ctx.caption(
            "68% containment radius of the Gaussian PSF of the FITS IRFs at the source offset, "
            "as a function of true energy. The official curves use the full point-spread "
            "distribution from the ROOT files.",
            "Official 68% containment radius vs true energy (AngResEtrue), from the full "
            "point-spread distribution.",
        ),
        ctx.finish(fig, ax), curves,
        "True gamma-ray energy E_T [TeV]", "Angular resolution (68% containment) [deg]",
        yscale="linear",
    )


@producer
def energy_resolution(ctx: Context):
    rel = ctx.release
    axis_type = rel.energy_resolution_axis
    xlabel = E_RECO_LABEL if axis_type == "reco_energy" else E_TRUE_LABEL
    fig, ax = new_figure((7, 5.5))
    curves = []
    for i, site in enumerate(ctx.sites):
        if not ctx.src.exists(site.key):
            continue
        curve = ctx.mask(site.key, ctx.src.energy_resolution(site.key)).with_label(site.label)
        draw_curve(ax, curve, i)
        curves.append(curve)
    if not curves:
        plt.close(fig)
        return
    ax.set(xscale="log", xlim=(1e-2, 300), ylim=(0, 0.3), xlabel=xlabel,
           ylabel=r"$\Delta E / E$ (68% containment)")
    ax.legend(loc="upper right", fontsize=14)
    which = "reconstructed" if axis_type == "reco_energy" else "true"
    yield FigureResult(
        "energy-resolution",
        f"Energy resolution ({_ref_label(rel)})",
        ctx.caption(
            "Half-width of the interval around 0 containing 68% of (E_R − E_T)/E_T, from the "
            "energy-dispersion matrix weighted by the effective area and an E^-2.62 spectrum, "
            f"in bins of {which} energy.",
            "Official energy resolution (histogram ERes of the ROOT files, whose y axis is "
            f"labelled 'RMS'), in bins of {which} energy.",
        ),
        ctx.finish(fig, ax), curves,
        "True gamma-ray energy E_T [TeV]" if axis_type == "true_energy" else "Reconstructed gamma-ray energy E_R [TeV]",
        "DeltaE / E (68% containment)", yscale="linear",
    )


def _aeff_figure(ctx: Context, site, direction_cut):
    rel = ctx.release
    fig, ax = new_figure((7, 5.5))
    curves = []
    for i, (label, duration) in enumerate(rel.durations.items()):
        if not ctx.src.exists(site.key, duration):
            continue
        curve = ctx.src.effective_area(site.key, duration, direction_cut=direction_cut)
        curve = curve.with_label(f"{site.label} ({label})")
        draw_curve(ax, curve, i)
        curves.append(curve)
    if not curves:
        plt.close(fig)
        return None
    ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=(1e2, 1e7),
           xlabel=E_TRUE_LABEL, ylabel=r"Effective area [m$^2$]")
    ax.legend(loc="lower right")
    ax.text(0.04, 0.93,
            "After gamma/hadron separation and direction cuts" if direction_cut
            else "After gamma/hadron separation cuts", transform=ax.transAxes)
    return ctx.finish(fig, ax), curves


@producer
def effective_area(ctx: Context):
    rel = ctx.release
    for site in ctx.sites:
        made = _aeff_figure(ctx, site, direction_cut=False)
        if made is None:
            continue
        fig, curves = made
        yield FigureResult(
            f"effective-area-{site.key}",
            f"{site.label}: effective area",
            ctx.caption(
                "Effective collection area after gamma/hadron separation, without cut on the "
                "reconstructed direction (the FITS IRFs are full-enclosure), read at the source "
                "offset from the FITS files, for each observation-time optimisation.",
                "Official effective area after gamma/hadron separation and without cut on the "
                "reconstructed direction (EffectiveAreaNoTheta2cut), for each observation-time "
                "optimisation.",
            ),
            fig, curves, "True gamma-ray energy E_T [TeV]", "Effective area [m2]",
        )


@producer(sources=("root",))
def effective_area_direction_cuts(ctx: Context):
    for site in ctx.sites:
        made = _aeff_figure(ctx, site, direction_cut=True)
        if made is None:
            continue
        fig, curves = made
        yield FigureResult(
            f"effective-area-direction-cuts-{site.key}",
            f"{site.label}: effective area with direction cut",
            "Official effective area after gamma/hadron separation and the optimised cut on the "
            "reconstructed direction (EffectiveArea). The FITS IRFs do not contain it.",
            fig, curves, "True gamma-ray energy E_T [TeV]", "Effective area [m2]",
        )


@producer
def background_rate(ctx: Context):
    rel = ctx.release
    fig, ax = new_figure((7, 5.5))
    curves = []
    for i, site in enumerate(ctx.sites):
        if not ctx.src.exists(site.key):
            continue
        curve = ctx.mask(site.key, ctx.src.background_rate(site.key)).with_label(site.label)
        draw_curve(ax, curve, i)
        curves.append(curve)
    if not curves:
        plt.close(fig)
        return
    ax.set(xscale="log", yscale="log", xlim=(1e-2, 300), ylim=(1e-5, 10),
           xlabel=E_RECO_LABEL, ylabel=r"Background rate [Hz deg$^{-2}$]")
    ax.legend(loc="upper right", fontsize=14)
    yield FigureResult(
        "background-rate",
        f"Residual background rate ({_ref_label(rel)})",
        ctx.caption(
            "Post-analysis cosmic-ray background rate per square degree near the centre of the "
            "field of view, integrated in 0.2-decade bins of reconstructed energy from the FITS "
            "background cube.",
            "Official residual background rate per square degree, in 0.2-decade bins of "
            "reconstructed energy (BGRatePerSqDeg: protons and electrons after the analysis cuts).",
        ),
        ctx.finish(fig, ax), curves,
        "Reconstructed gamma-ray energy E_R [TeV]", "Background rate [Hz deg-2]",
    )


# --------------------------------------------------------------------------
def _write(result: FigureResult, release: Release, source: str, out_dir: Path) -> dict:
    stem = out_dir / result.id
    result.figure.savefig(stem.with_suffix(".png"))
    plt.close(result.figure)
    header = [
        f"Release: {release.name} ({release.title}), doi:{release.doi}",
        f"Source: {SOURCES[source].title}",
        "Data: CTAO instrument response functions, CC BY 4.0. Not an official CTAO product "
        "unless the source says official.",
    ]
    stem.with_suffix(".dat").write_text(ascii_table(result, header), encoding="utf-8")
    stem.with_suffix(".py").write_text(plot_snippet(result, f"{result.id}.dat"), encoding="utf-8")
    return {
        "id": result.id,
        "title": result.title,
        "caption": result.caption,
        "source": source,
        "file": f"{source}/{result.id}.png",
        "data": f"{source}/{result.id}.dat",
        "script": f"{source}/{result.id}.py",
        "reference": release.reference_figures.get(result.id),
    }


def make_figures(release: Release, data_dir, out_dir, only=None, sources=ALL_SOURCES) -> list[dict]:
    """Run the producers for each source; save PNG + ASCII + snippet under ``out_dir/<source>/``.

    Returns the manifest, one entry per (source, figure). A source whose files are not
    downloaded is skipped with a warning.
    """
    manifest = []
    for source in sources:
        ctx = Context(release, data_dir, source)
        if not ctx.src.available():
            log.warning("%s: no %s data in %s, skipping that source "
                        "(`ctao-perf download%s %s`)", release.name, source, data_dir,
                        " --root" if source == "root" else "", release.name)
            continue
        out = Path(out_dir) / source
        out.mkdir(parents=True, exist_ok=True)
        for prod in PRODUCERS:
            if source not in prod.sources or (only and prod.__name__ not in only):
                continue
            try:
                for result in prod(ctx):
                    entry = _write(result, release, source, out)
                    log.info("%s: wrote %s", release.name, entry["file"])
                    manifest.append(entry)
            except FileNotFoundError as exc:
                log.warning("%s: skipping %s from %s (%s)", release.name, prod.__name__, source, exc)
    return manifest
