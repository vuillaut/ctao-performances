# Add a new IRF release

Everything downstream of the YAML file is generic, so a new release is one file
plus a check that it loads.

1. Copy the closest existing file:
   ```bash
   cp src/ctao_perf/releases/prod6-v1.0.yaml src/ctao_perf/releases/prod7-v1.0.yaml
   ```
2. Edit these keys (full list in the [release YAML reference](../reference/release-yaml.md)):
   - `name`, `title`, `configuration`, `description`, `doi`
   - `zenodo.record` and `zenodo.file`: the record number and the exact name of
     the zip to download. Pick the FITS-only zip if there is one.
   - `zenodo.root_file`: the zip with the ROOT files, if the record has one. Their names must follow
     `filename` with `.root`, otherwise set `root_filename`.
   - `filename`: the pattern of the FITS files **inside** the tarballs. Open one
     and copy its name, replacing the varying parts with `{site}`, `{zenith}`,
     `{azimuth}`, `{telescopes}`, `{condition}` and `{duration}`.
   - `sites.<key>.telescopes`: the telescope string as it appears in the file
     name (for example `2LSTs14MSTs37SSTs`).
   - `zeniths`, `durations` (label → seconds) and `reference_duration`.
   - `reference_figures`: names of the official PNGs shipped in the archive.
     Look in `data/<name>/archive/figures/`. Leave out those that do not exist.
3. Check that file names resolve:
   ```bash
   ctao-perf list
   ctao-perf download prod7-v1.0
   ls data/prod7-v1.0/irfs | head
   ```
   Then compare with `release.irf_filename("North", 180000)`.
4. Open one file and check the HDU names and `HDUCLAS4` values against
   [FITS contents](../data/fits-contents.md). `irfs.py` looks HDUs up through
   gammapy, which relies on `HDUCLAS*`, so a file that follows GADF works as is.
5. Decide `energy_resolution_axis`: `reco_energy` or `true_energy`, matching the
   axis of the official energy-resolution figure.
6. Add the release to the table in `README.md`, then run
   `ctao-perf figures prod7-v1.0` and look at the output.

CI picks up the new file on the next push: it downloads every bundled release
and publishes the site. The IRF cache key is a hash of `releases/*.yaml`, so
changing a YAML invalidates it.
