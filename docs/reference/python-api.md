# Python API

Public entry points. Everything is importable from `ctao_perf.<module>`.
Docstrings in the source carry the details.

## `ctao_perf`

| Name | Purpose |
|---|---|
| `load_release(name_or_path)` | Return a `Release` from a bundled name or a YAML path |
| `available_releases()` | All bundled releases, sorted by name |
| `Release`, `Site` | Dataclasses, see [release YAML](release-yaml.md) |

`Release` methods: `irf_filename(site, duration, zenith=None, azimuth=None, condition=None)`,
`duration_label(seconds)`, property `zenodo_url`.

## `ctao_perf.config`

`SensitivityCriteria(n_sigma=5, gamma_min=10, bkg_syst_fraction=0.05, alpha=0.2, containment=0.68)`.

## `ctao_perf.download`

| Function | Returns |
|---|---|
| `fetch(release, data_dir, force=False)` | Release folder; downloads and unpacks |
| `zenodo_file_info(record, filename)` | `(url, "md5:...")` from the Zenodo API |
| `release_dir`, `irf_dir`, `archive_dir` | `data/<name>`, `.../irfs`, `.../archive` |

`fetch_root(release, data_dir, force=False)`: download the ROOT bundle and extract the files listed by
`wanted_root_files(release)` into `root_dir(release, data_dir)`.

## `ctao_perf.irfs`

`IRFLibrary(release, data_dir)`:

| Method | Returns |
|---|---|
| `path(site, duration, **selection)` | `Path`; `FileNotFoundError` if absent |
| `exists(site, duration, **selection)` | `bool` |
| `load(site, duration, **selection)` | dict with `aeff`, `psf`, `edisp`, `bkg` (gammapy objects), cached per file |
| `provided_sensitivity(site, duration, **selection)` | `(energy_edges, theta_edges, e2dnde[theta, energy])` in erg cm⁻² s⁻¹, or `None` |

`selection` keywords: `zenith`, `azimuth`, `condition`.

`fill_edisp(edisp)`: copy the last populated migration column into empty ones at higher true energy. See [data caveats](../data/fits-contents.md#known-data-issues).

## `ctao_perf.performance`

All take the IRF dict from `IRFLibrary.load`. Quantities are astropy or plain
numpy as stated. `offset` defaults to 0.5°.

| Function | Returns |
|---|---|
| `sensitivity(irfs, livetime, location="ctao_south", energy_axis=None, offset=0.5 deg, criteria=None)` | `(energy_axis, e2dnde [erg cm⁻² s⁻¹], table)`; NaN where undefined |
| `angular_resolution(irfs, energy, offset, fraction=0.68)` | containment radius in deg at true energies; NaN where the PSF is empty |
| `psf_filled(psf, energy, offset)` | boolean array: true energy between the first and last PSF bin centres with non-zero parameters, at that offset |
| `energy_resolution(irfs, energy_edges, axis="reco_energy", offset, index=2.62, fraction=0.68)` | half-width of (E_R−E_T)/E_T, one value per bin |
| `effective_area(irfs, offset)` | `(true-energy axis, m²)` on the native binning |
| `background_rate(irfs, offset)` | `(reco-energy axis, Hz deg⁻²)` per native bin |
| `log_energy_axis(lo_exp=-1.9, hi_exp=2.3, per_decade=5)` | reconstructed-energy `MapAxis` |
| `single_bin_axis(energy, half_width_dex=0.1)` | one-bin axis centred on `energy` |
| `TRUE_ENERGY_AXIS` | true-energy axis, 0.005–500 TeV, 25 bins per decade, used for the exposure |

## `ctao_perf.curves`

`Curve(x, y, xlo=None, xhi=None, label="")`: one series of plain floats in the units of the figure axes.
Binned when `xlo`/`xhi` are given. `Curve.binned(edges, y, label)`, `.with_label()`, `.masked()`,
`.positive()`, `.name` (label without spaces).

## `ctao_perf.root`

Official curves from the ROOT files ([ROOT files](../data/root-files.md)). `RootLibrary(release, data_dir)`
with `path`, `exists`, `available`; `read_histogram(path, name)`; and readers that return a `Curve`:
`differential_sensitivity`, `angular_resolution(path, containment=68, energy="true")`,
`energy_resolution`, `effective_area(path, direction_cut=False)`, `background_rate`;
`differential_sensitivity_offaxis(path)` returns `(theta_edges, energy_edges, values)`.

## `ctao_perf.sources`

`GammapySource(release, data_dir)` and `RootSource(release, data_dir)`, with the same methods:
`exists`, `sensitivity(site, duration=None, ...)`, `sensitivity_offaxis`, `angular_resolution(site)`,
`energy_resolution(site)`, `effective_area(site, duration, direction_cut=False)`, `background_rate(site)`.
All return `Curve`s. `GammapySource` also has `load` and `sensitivity(..., livetime=, offset=,
energy_axis=)`. `RootSource` has no equivalent of the latter: only the sensitivity of the file.

## `ctao_perf.ascii`

`ascii_table(result, header_lines)` and `plot_snippet(result, data_file)`: the text of the `.dat`
file and of the script of a `FigureResult`. Format: [ASCII files](../how-to/use-the-ascii-files.md).

## `ctao_perf.figures`

`PRODUCERS` (list), `@producer(sources=...)`, `Context`, `FigureResult`,
`make_figures(release, data_dir, out_dir, only=None, sources=("gammapy", "root"))`.
See [Add a figure](../how-to/add-a-figure.md).

## `ctao_perf.plotting`

Matplotlib style and helpers: `new_figure`, `binned_points`, `finish`, `credit`,
`apply_style`, `draw_curve`, colour and label constants. Sets the `Agg` backend on import.

## `ctao_perf.site`

`build_release_page(release, manifest, data_dir, out)`, `build_index(entries, out)` and
`build_docs(docs_dir, out)` (Markdown to HTML).
