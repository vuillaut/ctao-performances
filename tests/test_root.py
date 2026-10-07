from pathlib import Path

import numpy as np
import pytest

uproot = pytest.importorskip("uproot")

from ctao_perf import load_release  # noqa: E402
from ctao_perf import root  # noqa: E402
from ctao_perf.download import wanted_root_files  # noqa: E402
from ctao_perf.root import RootLibrary, read_histogram  # noqa: E402

LOG_E = np.linspace(-1.9, 2.3, 22)  # 21 bins, five per decade


@pytest.fixture
def root_file(tmp_path):
    path = tmp_path / "irf.root"
    sens = np.linspace(1e-12, 1e-10, 21)
    sens[0] = 0  # empty bin
    with uproot.recreate(path) as f:
        f["DiffSens"] = (sens, LOG_E)
        f["AngResEtrue"] = (np.full(21, 0.05), LOG_E)
        f["ERes"] = (np.full(21, 0.1), LOG_E)
        f["BGRatePerSqDeg"] = (np.full(21, 2.0), LOG_E)
        f["EffectiveArea"] = (np.full(42, 1e5), np.linspace(-1.9, 2.3, 43))
        f["EffectiveAreaNoTheta2cut"] = (np.full(42, 2e5), np.linspace(-1.9, 2.3, 43))
        off = np.ones((21, 6))
        off[:, 3:] = 0  # only the first three offset bins are filled
        off[:, 1] = 2
        f["DiffSens_offaxis"] = (off, LOG_E, np.arange(7.0))
    read_histogram.cache_clear()
    return path


def test_differential_sensitivity_axes_and_empty_bins(root_file):
    curve = root.differential_sensitivity(root_file)
    assert curve.is_binned and len(curve.y) == 21
    assert np.isclose(curve.xlo[0], 10**-1.9) and np.isclose(curve.xhi[-1], 10**2.3)
    assert np.isnan(curve.y[0])  # zero in the file means "no value"
    assert curve.y[1] == pytest.approx(1e-12 + (1e-10 - 1e-12) / 20)


def test_effective_area_selects_direction_cut(root_file):
    assert root.effective_area(root_file, direction_cut=True).y[0] == 1e5
    assert root.effective_area(root_file, direction_cut=False).y[0] == 2e5
    assert not root.effective_area(root_file).is_binned  # drawn as a line


def test_offaxis_keeps_filled_bins(root_file):
    theta, e_edges, values = root.differential_sensitivity_offaxis(root_file)
    assert values.shape == (6, 21) and len(theta) == 7
    assert np.isnan(values[3:]).all()


def test_missing_histogram_message(root_file):
    with pytest.raises(KeyError, match="Nope"):
        read_histogram(root_file, "Nope")


def test_wanted_files_match_naming():
    release = load_release("prod6-v1.0")
    wanted = wanted_root_files(release)
    assert len(wanted) == 2 * len(release.zeniths) * len(release.durations)
    assert "Prod6-CTAO-South-52deg-AverageAz-2LSTs14MSTs37SSTs-dark-1800s-v1.0.root" in wanted


def test_root_filename_defaults_to_fits_pattern():
    release = load_release("prod5-v0.1")
    assert release.root_irf_filename("South", 18000) == (
        "Prod5-South-20deg-AverageAz-14MSTs37SSTs.18000s-v0.1.root")


def test_release_without_root_bundle_is_unavailable(tmp_path):
    """A release with no `zenodo.root_file` never uses ROOT files, even if some are on disk."""
    from dataclasses import replace

    release = replace(load_release("prod5-v0.1"), zenodo_root_file=None)
    (tmp_path / "prod5-v0.1" / "root").mkdir(parents=True)
    (tmp_path / "prod5-v0.1" / "root" / "x.root").write_bytes(b"")
    assert not RootLibrary(release, tmp_path).available()


def test_library_availability(tmp_path):
    release = load_release("prod6-v1.0")
    lib = RootLibrary(release, tmp_path)
    assert not lib.available()
    with pytest.raises(FileNotFoundError, match="download --root"):
        lib.path("South", 180000)


@pytest.mark.data
def test_prod6_gammapy_vs_root_sensitivity():
    """Our sensitivity stays within a few tens of percent of the official one (0.1-50 TeV)."""
    from ctao_perf.sources import GammapySource, RootSource

    release = load_release("prod6-v1.0")
    root_src, gammapy_src = RootSource(release, Path("data")), GammapySource(release, Path("data"))
    if not root_src.available():
        pytest.skip("ROOT files not downloaded (`ctao-perf download --root prod6-v1.0`)")
    for site in release.sites:
        ours, official = gammapy_src.sensitivity(site), root_src.sensitivity(site)
        assert np.allclose(ours.xlo, official.xlo, rtol=1e-3)  # same energy bins
        sel = (ours.x > 0.1) & (ours.x < 50)
        ratio = ours.y[sel] / official.y[sel]
        assert np.all((ratio > 0.9) & (ratio < 1.4)), (site, ratio)


@pytest.mark.data
def test_prod5_gammapy_vs_root_sensitivity():
    from ctao_perf.sources import GammapySource, RootSource

    release = load_release("prod5-v0.1")
    root_src, gammapy_src = RootSource(release, Path("data")), GammapySource(release, Path("data"))
    if not root_src.available():
        pytest.skip("ROOT files not downloaded (`ctao-perf download --root prod5-v0.1`)")
    for site in release.sites:
        ours, official = gammapy_src.sensitivity(site), root_src.sensitivity(site)
        sel = (ours.x > 0.1) & (ours.x < 50)
        ratio = ours.y[sel] / official.y[sel]
        assert np.all((ratio > 0.9) & (ratio < 1.4)), (site, ratio)
    # the official Prod5 South 50 h minimum is ~0.93e-13 erg cm-2 s-1
    assert 0.8e-13 < np.nanmin(root_src.sensitivity("South").y) < 1.1e-13


@pytest.mark.data
def test_prod6_root_angular_resolution_at_1tev():
    from ctao_perf.sources import RootSource

    release = load_release("prod6-v1.0")
    src = RootSource(release, Path("data"))
    if not src.available():
        pytest.skip("ROOT files not downloaded")
    curve = src.angular_resolution("South")
    i = int(np.argmin(np.abs(curve.x - 1.0)))
    assert 0.04 < curve.y[i] < 0.06


def test_fetch_root_keeps_bundle_when_nothing_matches(tmp_path):
    import io
    import tarfile
    import zipfile

    from ctao_perf.download import fetch_root

    release = load_release("prod6-v1.0")
    folder = tmp_path / release.name
    folder.mkdir()
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w:gz") as tf:
        info = tarfile.TarInfo("unrelated.root")
        info.size = 0
        tf.addfile(info, io.BytesIO())
    with zipfile.ZipFile(folder / release.zenodo_root_file, "w") as zf:
        zf.writestr("bundle/root/CTAO-Performance-x.ROOT.tar.gz", tar_bytes.getvalue())
    with pytest.raises(FileNotFoundError, match="none of the"):
        fetch_root(release, tmp_path)
    assert (folder / release.zenodo_root_file).exists()      # kept, so a later run can retry
    assert not (folder / ".root_unpacked").exists()          # no completion marker
