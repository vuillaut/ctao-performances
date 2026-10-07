"""Where the plotted numbers come from.

A *source* answers the same questions (sensitivity, resolutions, effective area, ...) from
different data, so every figure is drawn by the same code for each:

* :class:`GammapySource` recomputes them with gammapy from the FITS IRFs;
* :class:`RootSource` reads the official curves stored in the ROOT files.

Both return :class:`~ctao_perf.curves.Curve` objects in the units of the figure axes.
"""

from __future__ import annotations

import astropy.units as u
import numpy as np

from . import performance as perf
from . import root
from .config import Release
from .curves import Curve
from .irfs import IRFLibrary
from .root import RootLibrary


class GammapySource:
    name = "gammapy"
    title = "Reproduced with gammapy from the FITS IRFs"

    def __init__(self, release: Release, data_dir):
        self.release = release
        self.irfs = IRFLibrary(release, data_dir)
        self._cache = {}

    def available(self):
        return self.irfs.directory.is_dir()

    def exists(self, site, duration=None, **selection):
        return self.irfs.exists(site, duration or self.release.reference_duration, **selection)

    def load(self, site, duration=None, **selection):
        return self.irfs.load(site, duration or self.release.reference_duration, **selection)

    def sensitivity(self, site, duration=None, livetime=None, offset=None, energy_axis=None,
                    **selection) -> Curve:
        """Differential sensitivity; ``livetime`` defaults to the optimisation time."""
        duration = duration or self.release.reference_duration
        livetime = u.Quantity(livetime if livetime is not None else duration, "s")
        offset = self.release.offset if offset is None else u.Quantity(offset, "deg")
        key = (site, duration, livetime.value, offset.to_value("deg"),
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
            self._cache[key] = Curve.binned(axis.edges.to_value("TeV"), e2)
        return self._cache[key]

    def sensitivity_offaxis(self, site, duration=None):
        """``(offsets_deg, energy_centres_tev, values[offset, energy])``."""
        offsets = np.arange(0.5, 4.51, 0.25)
        curves = [self.sensitivity(site, duration, offset=o * u.deg) for o in offsets]
        return offsets, curves[0].x, np.array([c.y for c in curves])

    def angular_resolution(self, site) -> Curve:
        e_min = self.release.sites[site].e_min.to_value("TeV")
        energy = np.geomspace(e_min, 200, 200)
        r68 = perf.angular_resolution(self.load(site), energy * u.TeV, offset=self.release.offset)
        return Curve(energy, r68)

    def energy_resolution(self, site) -> Curve:
        edges = perf.log_energy_axis().edges
        res = perf.energy_resolution(self.load(site), edges, axis=self.release.energy_resolution_axis,
                                     offset=self.release.offset)
        return Curve.binned(edges.to_value("TeV"), res)

    def effective_area(self, site, duration=None, direction_cut=False) -> Curve:
        if direction_cut:
            raise FileNotFoundError("the FITS effective area has no direction cut")
        axis, aeff = perf.effective_area(self.load(site, duration), offset=self.release.offset)
        return Curve(axis.center.to_value("TeV"), aeff).positive()

    def background_rate(self, site) -> Curve:
        axis, rate = perf.background_rate(self.load(site), offset=self.release.offset)
        return Curve.binned(axis.edges.to_value("TeV"), rate).positive()


class RootSource:
    name = "root"
    title = "Official curves read from the ROOT files"

    def __init__(self, release: Release, data_dir):
        self.release = release
        self.library = RootLibrary(release, data_dir)

    def available(self):
        return self.library.available()

    def exists(self, site, duration=None, **selection):
        return self.library.exists(site, duration or self.release.reference_duration, **selection)

    def _path(self, site, duration=None, **selection):
        return self.library.path(site, duration or self.release.reference_duration, **selection)

    def sensitivity(self, site, duration=None, **selection) -> Curve:
        return root.differential_sensitivity(self._path(site, duration, **selection))

    def sensitivity_at_offset(self, site, offset, duration=None):
        """``DiffSens_offaxis`` in the 1° offset bin containing ``offset``: ``(Curve, (lo, hi))``.

        The FITS IRFs are this bin (bin 0, 0–1°, for the default 0.5° offset), whereas
        ``DiffSens`` is for a source on the camera axis.
        """
        theta, e_edges, values = root.differential_sensitivity_offaxis(self._path(site, duration))
        j = int(np.clip(np.searchsorted(theta, u.Quantity(offset, "deg").value, side="right") - 1,
                        0, len(theta) - 2))
        return Curve.binned(e_edges, values[j]), (theta[j], theta[j + 1])

    def sensitivity_offaxis(self, site, duration=None):
        theta, e_edges, values = root.differential_sensitivity_offaxis(self._path(site, duration))
        centres = 0.5 * (theta[:-1] + theta[1:])
        keep = np.isfinite(values).any(axis=1)  # offset bins with at least one value
        energy = np.sqrt(e_edges[:-1] * e_edges[1:])
        return centres[keep], energy, values[keep]

    def angular_resolution(self, site) -> Curve:
        return root.angular_resolution(self._path(site), energy="true")

    def energy_resolution(self, site) -> Curve:
        return root.energy_resolution(self._path(site))

    def effective_area(self, site, duration=None, direction_cut=False) -> Curve:
        return root.effective_area(self._path(site, duration), direction_cut=direction_cut)

    def background_rate(self, site) -> Curve:
        return root.background_rate(self._path(site))


SOURCES = {"gammapy": GammapySource, "root": RootSource}
