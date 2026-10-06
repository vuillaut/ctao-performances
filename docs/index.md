# ctao-perf documentation

`ctao-perf` rebuilds the CTAO performance figures from the public instrument
response functions (IRFs) on Zenodo, using [gammapy](https://gammapy.org).

The pages follow the [Diátaxis / Divio](https://docs.divio.com/documentation-system/)
split. Pick the section that matches what you need right now.

| I want to... | Go to | Kind |
|---|---|---|
| run the tool for the first time | [Getting started](tutorials/getting-started.md) | tutorial |
| compute a sensitivity from Python | [Your first sensitivity](tutorials/first-sensitivity.md) | tutorial |
| add a release, a figure, change a cut | [How-to guides](how-to/index.md) | how-to |
| look up a CLI flag, a YAML key, a function | [Reference](reference/index.md) | reference |
| understand why the code is built this way, and what the numbers mean | [Explanation](explanation/index.md) | explanation |
| know what is in the data files and where to find a value | [Data](data/index.md) | reference + explanation |

## Data in one paragraph

CTAO publishes each IRF release as a Zenodo record. `ctao-perf download` unpacks
it to `data/<release>/irfs/`, one FITS file per (site, zenith, azimuth, sky
condition, optimisation time). Each file holds the effective area, PSF, energy
dispersion and background as binary tables that follow the
[GADF](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/) IRF format, with
a few documented deviations. See [Data](data/index.md).
