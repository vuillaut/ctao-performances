# Architecture

```
releases/*.yaml ──► config.py ──► Release
                                    │
        download.py ◄───────────────┤ zenodo record, files
            │ data/<release>/irfs/*.fits.gz     data/<release>/root/*.root
            ▼                                          ▼
         irfs.py  (FITS → gammapy IRFs)           root.py  (uproot → Curve)
            │                                          │
            ▼                                          │
     performance.py  (IRFs → numbers)                  │
            │                                          │
            ▼                                          ▼
         sources.py:  GammapySource                RootSource      both return Curve
                                    │
                                    ▼
        figures.py  (@producer functions, Context.src) ──► PNG + .dat + .py + manifest
            │                  │                                   │
        plotting.py        ascii.py                         site.py ──► HTML (+ docs)
        (style)            (data file, script)                  ▲
                                                             cli.py
```

## Design choices

**A release is data, not code.** Prod5 and Prod6 differ in file naming, sites,
available zeniths and durations, but not in file structure. The YAML holds those
differences; the Python code has no `if release == ...`. The one switch that
remains, `energy_resolution_axis`, is also in the YAML because it follows how
CTAO plotted each release.

**`performance.py` knows nothing about releases.** Its functions take a dict of
gammapy IRFs and return numbers. That keeps them testable with synthetic IRFs and
reusable on files from other instruments that follow GADF.

**Two sources, one set of figures.** The same question ("what is the sensitivity of the South array
for 50 h?") is answered either by recomputing it with gammapy (`GammapySource`) or by reading the
official curve in the ROOT file (`RootSource`). Both return a `Curve`: plain arrays in the units of the
figure axes, binned or not. Producers ask `ctx.src` and draw `Curve`s, so each figure is drawn once, by
the same code, for both sources, and the two versions are directly comparable. Producers that need
the gammapy calculation (arbitrary livetime, ratio to the official value) say
`@producer(sources=("gammapy",))`.

**Plotted data are the data files.** `FigureResult.curves` holds the arrays that were drawn; `ascii.py` writes
the `.dat` file and the plot script from them. There is no second code path that could drift from the
figure.

**Figures are registered, not listed.** `@producer` appends to `PRODUCERS`; the
CLI and the website discover figures from that list. A producer that cannot find
its files is skipped, so a release that lacks a duration or a HDU still builds.

**Files are looked up from a pattern, not indexed.** The FITS files come without
an observation index or HDU index (see [GADF compliance](../data/gadf-compliance.md)),
so `IRFLibrary` builds the name from the release pattern and checks that the file
exists.

**Download is idempotent.** `.unpacked` marks a finished unpack. The Zenodo zip and
the tarballs are deleted once the FITS files are extracted, so a release takes
44 MB (Prod5) and 120 MB (Prod6) on disk.

## Caching

- `irfs._load` and `irfs._provided_sensitivity` use `lru_cache` (64 files), so
  each FITS file is read once per process; `root.read_histogram` does the same for ROOT histograms.
- `GammapySource.sensitivity` caches by `(site, duration, livetime, offset, energy axis,
  selection)`: the sensitivity is the slow step and several figures reuse it.

## Choices made in `irfs.py`

- gammapy reads Prod6 files with both a `PSF_3GAUSS` and a `PSF_TABLE` HDU. The
  code keeps what `load_irf_dict_from_file` returns (the Gaussian PSF), because the
  table is not normalised.
- `fill_edisp` repairs empty high-energy columns; see
  [known data issues](../data/fits-contents.md#known-data-issues).
