# Release YAML

One file per release in `src/ctao_perf/releases/`, loaded by
`ctao_perf.config.load_release` into a `Release` dataclass. Unknown top-level
keys raise a `TypeError`.

## Top-level keys

| Key | Type | Required | Meaning |
|---|---|---|---|
| `name` | str | yes | Short id, used as folder and CLI name |
| `title` | str | yes | Page title |
| `configuration` | str | yes | Array configuration name (Alpha, Beta) |
| `description` | str | no | Sentence shown on the website |
| `doi` | str | yes | DOI without the `https://doi.org/` prefix |
| `zenodo.record` | int | yes | Zenodo record number |
| `zenodo.file` | str | yes | Zip to download from that record (FITS only) |
| `zenodo.root_file` | str | no | Zip with the ROOT files, about 1 GB. Without it the release has FITS figures only |
| `filename` | str | yes | Pattern of the FITS files inside the tarballs (see below) |
| `root_filename` | str | no | Pattern of the ROOT files; default: `filename` with `.fits.gz` replaced by `.root` |
| `sites` | map | yes | See below |
| `zenith` | int | yes | Default zenith angle (deg) |
| `zeniths` | list[int] | yes | Available zenith angles; drives the zenith figure |
| `azimuth` | str | no | Default azimuth: `AverageAz` |
| `condition` | str | no | Default sky: `dark` |
| `durations` | map | yes | label → optimisation time in seconds |
| `reference_duration` | int | yes | Duration (s) of the "default" IRF (50 h = 180000) |
| `offset_deg` | float | no | Source offset in the field of view, default 0.5 |
| `energy_resolution_axis` | str | no | `reco_energy` (default) or `true_energy` |
| `short_term` | map | no | `duration` (s) and `energies_gev` for the sensitivity-vs-time figure; empty disables it |
| `offaxis` | map | no | `bins_tev`: list of `[lo, hi]` for the off-axis figure; empty disables it |
| `sensitivity` | map | no | [Criteria](../how-to/change-sensitivity-criteria.md) |
| `reference_figures` | map | no | figure id → official PNG name |

## `filename` placeholders

`{site}`, `{telescopes}`, `{zenith}`, `{azimuth}`, `{condition}`, `{duration}`.
`{telescopes}` comes from the site; the others from the call, falling back to
the release defaults. Prod5 has no `{condition}` in its names, so its pattern
does not use it.

## `sites.<key>`

| Key | Meaning |
|---|---|
| `label` | Legend text |
| `telescopes` | String used in file names for the full array |
| `location` | gammapy observatory key: `ctao_north` or `ctao_south` |
| `e_min_tev` | Lowest energy shown (the lowest of the official figure); lower bins are masked. Default 0.01 |
| `color` | Optional hex colour |

The site key (`North`, `South`) is also substituted into `{site}`.

## `sensitivity`

`n_sigma`, `gamma_min`, `bkg_syst_fraction`, `alpha`, `containment`. Defaults
and meaning in [Change the sensitivity criteria](../how-to/change-sensitivity-criteria.md).
