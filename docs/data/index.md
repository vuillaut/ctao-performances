# Data

The repository contains no data. IRFs are downloaded from Zenodo at run time.

- [Organisation of the files](#organisation-of-the-files) (this page)
- [File naming](file-naming.md): decode a file name, list what exists
- [FITS contents](fits-contents.md): HDUs, columns, axes, units, where each data point lives
- [ROOT files](root-files.md): the official curves; what they contain and how to read them
- [GADF compliance](gadf-compliance.md): what follows the community format, what does not

## What the data are

An instrument response function describes how the array turns a gamma ray into a
detected event. Each FITS file here holds four of them, sampled on a grid,
for **one** site, zenith angle, azimuth, sky condition and observation-time
optimisation:

| IRF | Answers | Tied to |
|---|---|---|
| Effective area | How large is the array for a gamma ray of energy E? | true energy, offset |
| Point spread function | How far from the true direction is it reconstructed? | true energy, offset |
| Energy dispersion | How does the reconstructed energy compare with the true one? | true energy, E_R/E_T, offset |
| Background | How many cosmic-ray events survive the cuts? | reconstructed energy, position in the field of view |

Prod6 FITS files add the official differential sensitivity. The ROOT files hold the official curves
themselves (sensitivity, resolutions, effective areas), see [ROOT files](root-files.md).

The cuts in these IRFs were optimised for flux sensitivity at a given
observation time, so there is one set per duration. They do not give the best
possible angular or energy resolution.

## Organisation of the files

### On Zenodo

| Release | Record | Zip downloaded by `ctao-perf` | Content |
|---|---|---|---|
| `prod5-v0.1` | [5499840](https://doi.org/10.5281/zenodo.5499840) | `cta-prod5-zenodo-fitsonly-v0.1.zip` | `fits/*.tar.gz` (18 tarballs), `figures/`, `README.md`, `Website.md`, `LICENSE` |
| `prod6-v1.0` | [22871179](https://doi.org/10.5281/zenodo.22871179) | `ctao-prod6-zenodo-v1.0-fits-only.zip` | `fits/*.tar.gz` (16 tarballs: 2 sites × 4 zeniths × 2 sky conditions), `figures/`, `README.md`, `Performance_report_prod6.md`, `LICENSE` |

Prod6 also has a bigger zip with ROOT files. `ctao-perf` uses the FITS-only one.
Each tarball groups similar files; Prod6 tarballs are named
`CTAO-Performance-Prod6-CTAO-<site>-<zenith>deg-<condition>-v1.0.FITS.tar.gz`.

### On your disk

After `ctao-perf download` (default `--data-dir data`, ignored by git):

```
data/
  prod5-v0.1/
    .unpacked              file count, written when the unpack succeeds
    irfs/                  162 files, flat
      Prod5-South-20deg-AverageAz-14MSTs37SSTs.180000s-v0.1.fits.gz
      ...
    archive/               unpacked zip, minus the tarballs
      README.md  Website.md  LICENSE
      figures/*.png        official figures
  prod6-v1.0/
    .unpacked
    irfs/                  192 files, flat
    archive/ctao-prod6-zenodo-v1.0-fits-only/
      README.md  Performance_report_prod6.md  LICENSE
      figures/*.png
```

The tarballs are flattened into `irfs/`, then deleted, together with the zip.

With `ctao-perf download --root`, the ROOT files are added (Prod6 shown; Prod5 has 18 files):

```
data/prod6-v1.0/
  root/                    32 files: 2 sites x 4 zeniths x 4 durations, AverageAz, dark
    Prod6-CTAO-South-20deg-AverageAz-2LSTs14MSTs37SSTs-dark-180000s-v1.0.root
  .root_unpacked
```

They come from a separate Zenodo zip (1.1 GB for Prod6, 0.9 GB for Prod5), of which only these files are kept
(about 205 MB and 137 MB).
`archive/` stays because the website copies the official figures from it.

### What the numbers of files mean

| | Prod5 | Prod6 |
|---|---|---|
| Sites | North, South | North, South |
| Arrays per site | 3 (full array and two sub-arrays) | 1 (full array) |
| Zenith angles | 20°, 40°, 60° | 20°, 40°, 52°, 60° |
| Azimuths | AverageAz, NorthAz, SouthAz | AverageAz, NorthAz, SouthAz |
| Sky | dark only (not in file name) | dark, halfmoon |
| Optimisation times | 1800 s, 18000 s, 180000 s | 100 s, 1800 s, 18000 s, 180000 s |
| **Files** | 2 × 3 × 3 × 3 × 3 = **162** | 2 × 4 × 3 × 2 × 4 = **192** |

Read next: [File naming](file-naming.md).

## Licence and credit

CTAO IRFs are released under CC BY 4.0. Cite the Zenodo DOI of the release and
add the acknowledgement requested in the [README](https://github.com/vuillaut/ctao-performances#citation).
