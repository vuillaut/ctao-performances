"""Release descriptions.

Each IRF release published by CTAO is described by a YAML file (see the
``releases/`` folder of the package). Supporting a new release means adding a
new YAML file: the download, IRF lookup, computations and figures are generic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

import astropy.units as u
import yaml

RELEASES_PACKAGE = "ctao_perf.releases"


@dataclass
class Site:
    key: str
    label: str
    telescopes: str
    location: str
    e_min: u.Quantity
    color: str = "#444444"


@dataclass
class SensitivityCriteria:
    n_sigma: float = 5.0
    gamma_min: float = 10.0
    bkg_syst_fraction: float = 0.05
    alpha: float = 0.2
    containment: float = 0.68


@dataclass
class Release:
    name: str
    title: str
    configuration: str
    doi: str
    zenodo_record: int
    zenodo_file: str
    filename: str
    sites: dict[str, Site]
    durations: dict[str, int]
    reference_duration: int
    zenith: int
    zeniths: list[int]
    azimuth: str = "AverageAz"
    condition: str = "dark"
    offset: u.Quantity = 0.5 * u.deg
    # "reco_energy" or "true_energy": energy axis of the energy-resolution figure
    energy_resolution_axis: str = "reco_energy"
    short_term: dict = field(default_factory=dict)
    offaxis: dict = field(default_factory=dict)
    sensitivity: SensitivityCriteria = field(default_factory=SensitivityCriteria)
    reference_figures: dict[str, str] = field(default_factory=dict)
    description: str = ""
    source: Path | None = None
    # Zenodo bundle with the ROOT files, and their naming pattern (defaults to the FITS
    # pattern with the extension replaced)
    zenodo_root_file: str | None = None
    root_filename: str | None = None

    @property
    def zenodo_url(self):
        return f"https://zenodo.org/records/{self.zenodo_record}"

    def duration_label(self, seconds):
        for label, value in self.durations.items():
            if value == seconds:
                return label
        return f"{seconds} s"

    def irf_filename(self, site, duration, zenith=None, azimuth=None, condition=None):
        """File name of one FITS IRF, following the release naming pattern."""
        return self._format(self.filename, site, duration, zenith, azimuth, condition)

    def root_irf_filename(self, site, duration, zenith=None, azimuth=None, condition=None):
        """File name of the ROOT file holding the official curves for one IRF."""
        pattern = self.root_filename or re.sub(r"\.fits(\.gz)?$", ".root", self.filename)
        return self._format(pattern, site, duration, zenith, azimuth, condition)

    def _format(self, pattern, site, duration, zenith, azimuth, condition):
        return pattern.format(
            site=site,
            telescopes=self.sites[site].telescopes,
            zenith=self.zenith if zenith is None else zenith,
            azimuth=azimuth or self.azimuth,
            condition=condition or self.condition,
            duration=duration,
        )


def _quantity(value, unit):
    return u.Quantity(value, unit)


def load_release(path_or_name) -> Release:
    """Load a release from a YAML path or from the name of a bundled release."""
    path = Path(path_or_name)
    if not path.exists():
        path = Path(str(resources.files(RELEASES_PACKAGE) / f"{path_or_name}.yaml"))
    if not path.exists():
        names = ", ".join(r.name for r in available_releases())
        raise FileNotFoundError(f"Unknown release {path_or_name!r}. Bundled releases: {names}")

    cfg = yaml.safe_load(path.read_text())
    sites = {
        key: Site(
            key=key,
            label=s["label"],
            telescopes=s["telescopes"],
            location=s["location"],
            e_min=_quantity(s.get("e_min_tev", 0.01), "TeV"),
            color=s.get("color", "#444444"),
        )
        for key, s in cfg.pop("sites").items()
    }
    zenodo = cfg.pop("zenodo")
    root_file = zenodo.get("root_file")
    sensitivity = SensitivityCriteria(**cfg.pop("sensitivity", {}))
    offset = _quantity(cfg.pop("offset_deg", 0.5), "deg")
    return Release(
        sites=sites,
        zenodo_record=zenodo["record"],
        zenodo_file=zenodo["file"],
        zenodo_root_file=root_file,
        sensitivity=sensitivity,
        offset=offset,
        source=path,
        **cfg,
    )


def available_releases() -> list[Release]:
    """All releases bundled with the package, sorted by name."""
    folder = resources.files(RELEASES_PACKAGE)
    paths = sorted(Path(str(p)) for p in folder.iterdir() if p.name.endswith(".yaml"))
    return [load_release(p) for p in paths]
