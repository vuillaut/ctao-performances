# CTAO performances

Reproduce the performance figures of the Cherenkov Telescope Array Observatory
(CTAO) from the instrument response functions (IRFs) published on Zenodo, using
[gammapy](https://gammapy.org).

The figures are rebuilt by CI and published at
**https://vuillaut.github.io/ctao-performances/**, next to the official
figures shipped with each release.

Supported releases:

| Release | Configuration | Zenodo |
|---|---|---|
| `prod5-v0.1` | Alpha (North: 4 LST + 9 MST, South: 14 MST + 37 SST) | [10.5281/zenodo.5499840](https://doi.org/10.5281/zenodo.5499840) |
| `prod6-v1.0` | Beta (North: 4 LST + 9 MST, South: 2 LST + 14 MST + 37 SST) | [10.5281/zenodo.22871179](https://doi.org/10.5281/zenodo.22871179) |

## Usage

```bash
pip install -e .            # or: uv pip install -e .
ctao-perf list              # bundled releases and figure producers
ctao-perf download prod6-v1.0
ctao-perf figures prod6-v1.0 -o figures
ctao-perf site              # download + figures + static website in ./public
```

IRFs are downloaded to `./data/<release>/` (change with `--data-dir`).
`--only sensitivity_durations energy_resolution` restricts the figures.

The building blocks can also be used directly:

```python
import astropy.units as u
from ctao_perf import load_release
from ctao_perf.irfs import IRFLibrary
from ctao_perf import performance as perf

release = load_release("prod6-v1.0")
irfs = IRFLibrary(release, "data").load("South", 180000, zenith=40)
axis, e2dnde, table = perf.sensitivity(irfs, livetime=50 * u.h, location="ctao_south")
```

## Layout

```
src/ctao_perf/
  releases/*.yaml   one file per IRF release (Zenodo record, file naming, sites, ...)
  config.py         Release / Site dataclasses, YAML loading
  download.py       Zenodo download, checksum, unpacking of the tarballs
  irfs.py           IRF lookup from the naming pattern, loading and fixes
  performance.py    release-independent computations (sensitivity, resolutions, ...)
  plotting.py       shared matplotlib style
  figures.py        figure producers (registered with @producer)
  site.py           static website
  cli.py            `ctao-perf` command
```

### Adding a new IRF release

Copy one of the YAML files in `src/ctao_perf/releases/`, then adapt the Zenodo
record and file name, the `filename` pattern of the individual FITS files, the
telescope string of each site, the available zenith angles and durations, and
the mapping to the official figures. Every figure producer then runs on the new
release, and CI publishes it.

### Adding a figure

Write a generator in `figures.py` decorated with `@producer` that takes a
`Context` and yields `FigureResult`s. It runs for every release.

## Method

The sensitivity is computed with `gammapy.estimators.SensitivityEstimator`: on
region set to the 68% PSF containment radius, off/on exposure ratio 5,
5σ detection, at least 10 excess events and S/B ≥ 5%, in five bins per decade
of reconstructed energy. Energy resolution is the 68% half-width of
(E_R − E_T)/E_T, weighted by the effective area and an E^-2.62 spectrum.

The official figures are produced from the full simulations with cuts
optimised per energy bin, and from the ROOT files for the PSF. Expect
differences of tens of percent near the energy threshold and at the highest
energies. Where a release ships its official sensitivity in the FITS files
(Prod6), a validation figure compares both.

Known data issues handled in `irfs.py`: empty energy-dispersion columns at
the highest energies (e.g. prod5 North 50 h) are filled with the last
populated column.

## Citation

See [`CITATION.cff`](CITATION.cff) (GitHub's "Cite this repository" button).
If you use the figures or the code, please also cite the IRF releases and
include the acknowledgements requested by CTAO:

- prod5 v0.1, [doi:10.5281/zenodo.5499840](https://doi.org/10.5281/zenodo.5499840):
  "This research has made use of the CTA instrument response functions
  provided by the CTA Observatory and Consortium, see
  https://www.cta-observatory.org/science/cta-performance/ (version prod5 v0.1;
  https://doi.org/10.5281/zenodo.5499840) for more details."
- Prod6 v1.0, [doi:10.5281/zenodo.22871179](https://doi.org/10.5281/zenodo.22871179):
  "This research has made use of the CTAO Prod6 instrument response functions,
  Prod6 v1.0, provided by the CTAO and archived at
  https://doi.org/10.5281/zenodo.22871179." CTAO also asks to cite CORSIKA,
  sim_telarray, the Prod6 telescope model, Eventdisplay and Eventdisplay-ML;
  see the BibTeX file shipped with the record.

The computations use [gammapy](https://gammapy.org)
([Donath et al. 2023, A&A 678, A157](https://doi.org/10.1051/0004-6361/202346488)).

## License

- Code: [BSD 3-Clause](LICENSE).
- Data: the CTAO instrument response functions are distributed by CTAO under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). They are downloaded
  from Zenodo at run time and are not included in this repository.
- Figures: the generated figures are derived from those IRFs and are shared
  under CC BY 4.0, with attribution to CTAO and the DOI of the release. The
  official figures shown for comparison on the website come unmodified from the
  same Zenodo records, also under CC BY 4.0.

These figures are not official CTAO products.
