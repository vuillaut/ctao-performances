# Getting started

By the end of this page you will have downloaded the Prod6 IRFs, produced the
figures and opened them. Plan for about five minutes and 120 MB of disk.

## 1. Install

```bash
git clone https://github.com/vuillaut/ctao-performances
cd ctao-performances
pip install -e .          # or: uv pip install -e .
```

Python 3.10 or later is required. gammapy 2.1 and its dependencies come with it.

## 2. See what is bundled

```bash
ctao-perf list
```

```
prod5-v0.1     CTAO prod5 v0.1 (Alpha configuration)  (zenodo 5499840)
prod6-v1.0     CTAO Prod6 v1.0 (Beta configuration)  (zenodo 22871179)

figure producers: sensitivity_durations, sensitivity_north_south, ...
```

## 3. Download one release

```bash
ctao-perf download prod6-v1.0
```

This fetches a zip from Zenodo, checks its MD5, unpacks the tarballs and keeps
only the FITS files. You get:

```
data/prod6-v1.0/
  irfs/      192 FITS files
  archive/   README, performance report and the official PNG figures
  .unpacked  marker: the next run skips the download
```

## 4. Make the figures

```bash
ctao-perf figures prod6-v1.0 -o figures
```

PNG files land in `figures/prod6-v1.0/gammapy/`. Start with
`gammapy/sensitivity-north-south.png`, the differential sensitivity of both arrays for
50 h. The run takes a few minutes: the sensitivity is computed in each energy
bin for each curve.

To try something faster, restrict to one figure:

```bash
ctao-perf figures prod6-v1.0 --only angular_resolution
```

## 5. Add the official curves (optional)

The ROOT files of the release hold the curves behind the official figures. They are in a 1.1 GB
bundle (0.9 GB for Prod5), of which about 205 MB (137 MB for Prod5) are kept:

```bash
ctao-perf download --root prod6-v1.0
ctao-perf figures prod6-v1.0 -o figures
```

`figures/prod6-v1.0/` now has two folders, `gammapy/` and `root/`. Each figure comes with a `.dat`
file of its points and a `.py` script to plot it again. Compare
`gammapy/sensitivity-north-south.png` with `root/sensitivity-north-south.png`.

## 6. Build the website (optional)

```bash
ctao-perf site            # download (FITS + ROOT) + figures + docs, in ./public
open public/index.html
```

Each release page shows, for each figure, the gammapy figure, the official curves from ROOT and
the official PNG from the Zenodo archive, with the data points to download. The documentation is
in `public/docs/`.

## Next

- Compute your own numbers: [Your first sensitivity](first-sensitivity.md).
- Look inside a file: [FITS contents](../data/fits-contents.md), [ROOT files](../data/root-files.md).
- Why the two kinds of figures differ: [Differences](../explanation/differences-from-official.md).
