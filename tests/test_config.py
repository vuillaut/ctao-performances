import pytest

from ctao_perf import available_releases, load_release
from ctao_perf.figures import PRODUCERS


def test_bundled_releases():
    names = [r.name for r in available_releases()]
    assert "prod5-v0.1" in names
    assert "prod6-v1.0" in names


@pytest.mark.parametrize(
    "name, args, expected",
    [
        ("prod5-v0.1", ("South", 180000), "Prod5-South-20deg-AverageAz-14MSTs37SSTs.180000s-v0.1.fits.gz"),
        ("prod5-v0.1", ("North", 18000), "Prod5-North-20deg-AverageAz-4LSTs09MSTs.18000s-v0.1.fits.gz"),
        ("prod6-v1.0", ("North", 18000), "Prod6-CTAO-North-20deg-AverageAz-4LSTs09MSTs-dark-18000s-v1.0.fits.gz"),
    ],
)
def test_filename_pattern(name, args, expected):
    assert load_release(name).irf_filename(*args) == expected


def test_filename_selection():
    release = load_release("prod6-v1.0")
    name = release.irf_filename("South", 180000, zenith=40, azimuth="NorthAz", condition="halfmoon")
    assert name == "Prod6-CTAO-South-40deg-NorthAz-2LSTs14MSTs37SSTs-halfmoon-180000s-v1.0.fits.gz"


def test_reference_figures_have_producers():
    """Every official figure referenced in a YAML maps to a figure id we produce."""
    prefixes = {
        "sensitivity-durations", "sensitivity-north-south", "angular-resolution",
        "energy-resolution", "effective-area", "background-rate", "offaxis-sensitivity",
        "sensitivity-time",
    }
    for release in available_releases():
        for fig_id in release.reference_figures:
            assert any(fig_id.startswith(p) for p in prefixes), fig_id
    assert len(PRODUCERS) >= 10


def test_unknown_release():
    with pytest.raises(FileNotFoundError):
        load_release("prod42")
