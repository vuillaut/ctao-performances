# FITS contents

What is in a file, and where to find each number. Checked on
`Prod6-CTAO-South-20deg-AverageAz-2LSTs14MSTs37SSTs-dark-180000s-v1.0.fits.gz`
and `Prod5-South-20deg-AverageAz-14MSTs37SSTs.180000s-v0.1.fits.gz`.
The HDU names, column shapes and `HDUVERS` were checked on all 162 Prod5 and
192 Prod6 files: they are identical within a release.

Every IRF is a binary table with **one row**. Axes and data are array columns of
that row, so you read `hdul["EFFECTIVE AREA"].data[0]["EFFAREA"]`. See
[Read the FITS directly](../how-to/read-fits-directly.md) for code.

## HDU list

Look HDUs up by name; the order differs between releases.

| # Prod5 | # Prod6 | `EXTNAME` | `HDUCLAS4` | Content |
|---|---|---|---|---|
| 0 | 0 | `PRIMARY` | | empty; `TELESCOP`, `INSTRUME`, `AUTHOR` |
| 1 | 1 | `EFFECTIVE AREA` | `AEFF_2D` | effective area |
| 2 | 2 | `POINT SPREAD FUNCTION` | `PSF_3GAUSS` | PSF |
| – | 3 | `PSF_TABLE` | `PSF_TABLE` | tabulated PSF (Prod6 only) |
| 3 | 4 | `ENERGY DISPERSION` | `EDISP_2D` | energy migration |
| 4 | 5 | `BACKGROUND` | `BKG_3D` | background rate |
| – | 6 | `DIFFERENTIAL SENSITIVITY` | `DIFFSENS_2D` | official sensitivity (Prod6 only) |

Header keywords common to all IRF HDUs: `HDUCLASS=GADF`, `HDUDOC` (the GADF
repository URL), `HDUVERS=0.2`, `HDUCLAS1=RESPONSE`, `HDUCLAS3=FULL-ENCLOSURE`,
`TELESCOP=CTA`, `INSTRUME` (`CTAO Southern Array`/`CTAO Northern Array`; Prod5:
`Southern Array`), `ORIGIN=CTAO`, `AUTHOR`, `DATE`. `HDUCLAS2` is `EFF_AREA`, `PSF`,
`EDISP`, `BKG`; the sensitivity HDU has none. The background HDU also has
`FOVALIGN=RADEC`.

## The axes

| Axis | Columns | Unit | Where | Bins |
|---|---|---|---|---|
| True energy, effective area | `ENERG_LO/HI` | TeV | `EFFECTIVE AREA` | 42, 0.0126–200 TeV (10 per decade) |
| True energy, PSF | `ENERG_LO/HI` | TeV | `POINT SPREAD FUNCTION` | 21, 0.0126–200 TeV (5 per decade) |
| True energy, PSF table | `ENERG_LO/HI` | TeV | `PSF_TABLE` | 25, 0.0126–1259 TeV |
| True energy, edisp | `ENERG_LO/HI` | TeV | `ENERGY DISPERSION` | 300, 0.01–10⁴ TeV |
| Migration E_R/E_T | `MIGRA_LO/HI` | – | `ENERGY DISPERSION` | 300, 0–3 (width 0.01) |
| Reconstructed energy | `ENERG_LO/HI` | TeV | `BACKGROUND`, `DIFFERENTIAL SENSITIVITY` | 21, 0.0126–200 TeV (5 per decade) |
| Offset | `THETA_LO/HI` | deg | aeff, psf, edisp, sensitivity | 6, 0–6, width 1° |
| Detector x, y | `DETX_LO/HI`, `DETY_LO/HI` | deg | `BACKGROUND` | 60 each, −6 to 6, width 0.2° |
| Radius | `RAD_LO/HI` | deg | `PSF_TABLE` | 9000, 0–4.5, width 0.0005° |

Numbers are from the Prod6 South file above; Prod5 has the same grids except
where noted below. The energy axes of Prod5 and Prod6 are the same
(10^-1.9 TeV = 0.0126 TeV is the lowest edge).

<a id="the-offset-axes"></a>
### The offset axes

`THETA` is the angle from the pointing direction, in 1° bins labelled by lower and upper
edge (`0–1`, `1–2`, …). The default source offset of this repository, 0.5°, sits
at the centre of the first bin. gammapy interpolates between bin centres for
other offsets.

`BACKGROUND` is a 2-D map in detector coordinates, not a function of offset:
`DETX`, `DETY` are field-of-view coordinates aligned with RA/Dec (`FOVALIGN=RADEC`).
This code reads it along `DETY = 0` at `DETX = offset`.

Not every offset bin is filled. In the Prod6 South 50 h file, effective area,
PSF and energy dispersion are non-zero in all six bins, but the
`DIFFERENTIAL SENSITIVITY` is non-zero only in the first three (0–3°).

## Where is…

| I want | HDU | Column | Unit | Axes → numpy shape |
|---|---|---|---|---|
| effective area | `EFFECTIVE AREA` | `EFFAREA` | m² | (theta, E_true) = (6, 42) |
| uncertainty on the effective area (Prod6; its definition is not given in the file) | `EFFECTIVE AREA` | `EFFAREA_ERR` | m² | (6, 42) |
| PSF width, first Gaussian | `POINT SPREAD FUNCTION` | `SIGMA_1` | deg | (6, 21) |
| PSF normalisation | `POINT SPREAD FUNCTION` | `SCALE` | sr⁻¹ | (6, 21) |
| other Gaussians | `POINT SPREAD FUNCTION` | `SIGMA_2`, `SIGMA_3`, `AMPL_2`, `AMPL_3` | deg, – | (6, 21), all zero |
| radial PSF (Prod6) | `PSF_TABLE` | `RPSF` | sr⁻¹ | (6, 9000, 25) = (theta, rad, E_true) |
| energy dispersion | `ENERGY DISPERSION` | `MATRIX` | – | (6, 300, 300) = (theta, migra, E_true) |
| background rate | `BACKGROUND` | `BKG` | s⁻¹ MeV⁻¹ sr⁻¹ | (60, 60, 21) = (dety, detx, E_reco)* |
| official diff. sensitivity (Prod6) | `DIFFERENTIAL SENSITIVITY` | `DIFFSENS` | erg cm⁻² s⁻¹ | (6, 21) = (theta, E_reco) |
| energy threshold | – | not stored | | see below |

\* Check the `TDIM` keyword of the column: FITS lists the fastest axis first
(`BKG` is `(21,60,60)`, so the numpy order is the reverse, and the first numpy
axis is the one listed last).

Everything is stored as 32-bit floats.

## Point spread function

`PSF_3GAUSS` is defined as a sum of three Gaussians. In all the files checked
(Prod5 and Prod6), `SIGMA_2`, `SIGMA_3`, `AMPL_2` and `AMPL_3` are zero: the PSF is
a **single** Gaussian given by `SIGMA_1` and `SCALE`. The release notes say so:
FITS uses a Gaussian approximation, ROOT keeps the full distribution.

Prod6 files also hold `PSF_TABLE`, a radial profile in 9000 bins. A comment in
`irfs.py` says the table is not normalised, so `ctao-perf` ignores it and gammapy
keeps the Gaussian PSF.

## Energy dispersion

`MATRIX` is the probability that a gamma ray of a given true energy and offset
lands in each migration bin, μ = E_R/E_T. In the Prod6 South file, for every
populated true-energy bin it sums to 1 over the migration axis (probability per
bin, not per unit μ; the bins are 0.01 wide). The numpy axis order is
`(theta, migra, E_true)`, the reverse of `TDIM = (300,300,6)`. True-energy bins
the simulation did not populate are all zero (see below).

## Background

`BKG` is the post-cut cosmic-ray rate, absolute, per MeV and per steradian
(although energies are in TeV). `ctao-perf` multiplies it by the bin width in MeV
(the TeV width × 10⁶) to get Hz sr⁻¹, then by (π/180)² sr deg⁻² to get Hz deg⁻².

## Differential sensitivity (Prod6 only)

`DIFFSENS` is E² dN/dE in erg cm⁻² s⁻¹, per reconstructed-energy bin and offset bin,
for the observation time in the file name. Zero entries exist (all the
bins above 3° in the file inspected); `ctao-perf` turns values ≤ 0 into NaN.

## Energy threshold

The files do not carry the optional `LO_THRES`/`HI_THRES` keywords. `ctao-perf`
uses a per-site lowest energy (`e_min_tev` in the release YAML) taken from the
official figures, to mask bins below the plotted range.

<a id="known-data-issues"></a>
## Known data issues

- **Empty energy-dispersion columns at high energy.** Some files, for example Prod5
  North 50 h, have no entries in `MATRIX` above about 120 TeV while the effective
  area is non-zero there. gammapy would then lose these events. `irfs.fill_edisp`
  copies the last populated migration distribution into the empty higher-energy
  rows. This is a patch applied at load time; the file on disk is unchanged.
- **`PSF_3GAUSS` is a single Gaussian** in every file, although the HDU can hold
  three. Do not read `SIGMA_2/3` expecting a tail.
