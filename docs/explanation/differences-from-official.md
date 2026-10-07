# Why the gammapy figures differ from the official ones

The gammapy curves are not the official ones. This page says, curve by curve, what is computed,
what is approximated and how large the gap is. The gaps are measured against the official curves in
the ROOT files, for Prod6 v1.0 and Prod5 v0.1 (South and North, 50 h, zenith 20°, `AverageAz`, dark sky
for Prod6). The tables below are for Prod6; Prod5 is [at the end of the next section](#prod5-v01).

The gammapy calculation uses only the FITS files, by design: anyone with the FITS IRFs can reproduce
it. Part of the gap to the official curves comes from information that is in the ROOT files but not in
the FITS files, and it cannot be removed without giving up this choice
([Limitation of a FITS-only calculation](#limitation-of-a-fits-only-calculation)).

Ratios are *gammapy / official*, over 0.1–50 TeV, the range where the analysis has good statistics
([ratio figures](../reference/figures.md)). "Median" is the median over the energy bins.

| Curve | What is computed | Median ratio (North / South) | Range | Where it gets worse |
|---|---|---|---|---|
| Differential sensitivity | gammapy `SensitivityEstimator` on an on/off dataset built from the FITS IRFs | 1.06 / 1.08 | 0.99–1.14 / 0.99–1.29 | below 0.04 TeV, above 10 TeV |
| Angular resolution | 68 % containment radius of the Gaussian PSF | 1.01 / 1.00 | 0.87–1.08 / 0.93–1.07 (0.02–40 TeV) | North: no value above 63 TeV (empty PSF) |
| Energy resolution | 68 % half-width of (E_R − E_T)/E_T from the migration matrix | 1.01 / 1.09 | 0.79–1.16 / 0.95–1.20 | first and last bins |
| Background rate | `BKG` cube integrated per bin, at 0.5° | 1.00 / 1.01 | 0.94–1.00 / 1.00–1.08 | |
| Effective area | `EFFAREA` at 0.5°, no direction cut | 0.96 / 0.98 | 0.78–1.07 / 0.88–1.08, vs the ROOT area without direction cut | |

A sensitivity ratio above 1 means the gammapy sensitivity is worse (a larger flux is needed). In the
middle of the range it is 5–8 % above the official on-axis curve, and 2–5 % above the official curve for
a source between 0° and 1° from the camera centre, which is the case the FITS IRFs describe. The
[next section](#differential-sensitivity) gives the causes and the share of each.

## Prod5 v0.1

Same measurement, same code, on the Prod5 files (energy resolution on reconstructed energy, as the
release YAML says). Ratios *gammapy / official* over 0.1–50 TeV, median (range), North / South:

| Curve | North | South |
|---|---|---|
| Differential sensitivity | 1.05 (1.01–1.22) | 1.06 (0.99–1.28) |
| Differential sensitivity, 50–200 TeV | 1.43 (1.31–9.0) | 1.36 (1.23–1.52) |
| Angular resolution, 0.02–60 TeV | 1.00 (0.97–1.07) | 0.98 (0.93–1.01) |
| Energy resolution | 1.08 (0.99–1.13) | 1.03 (0.97–1.14) |
| Background rate | 1.00 (0.93–1.00) | 1.00 (1.00–1.02) |
| Effective area (no direction cut) | 0.99 (0.91–1.22) | 0.99 (0.92–1.17) |

Same picture as Prod6, with these differences:

- Above 50 TeV the gammapy sensitivity is further from the official one than for Prod6 (a factor 9 for
  North in the last bin, 126–200 TeV). The main cause is the minimum radius of the official direction cut
  ([cause 3](#3-on-region-and-direction-cut)).
- Near the threshold the ratio is below 1: 0.76 and 0.84 in the bins centred at 0.025 and 0.04 TeV for
  North, and 0.85 in the 0.063 TeV bin for South (its first bin shown). The on region is smaller than the
  official cut there ([cause 3](#3-on-region-and-direction-cut)).
- The angular resolution holds up to the highest energies for South, and to 0.79 at 158 TeV for North,
  better than for Prod6 North.
- The official Prod5 energy-resolution figure is a smooth curve; the ROOT file has one value per bin, so
  both curves on the site are binned. The ROOT values agree with the smooth curve (about 0.07 at 1 TeV
  and 0.06 at 5 TeV for South).
- The Prod5 FITS files have no `DIFFERENTIAL SENSITIVITY` HDU: the ROOT file is the only official
  sensitivity. The validation figures use the ROOT file for both references (0–1° and on axis).

## Differential sensitivity

### The official calculation

`DiffSens` in the ROOT file is computed by Eventdisplay. The `IRFLog` object of the same file records,
for each energy bin, the inputs and the result. From this log:

- The signal comes from gamma rays simulated as a point source **on the camera axis**
  (`gamma_onSource` files). The protons and electrons are diffuse.
- Counts are computed for the Crab Nebula spectrum of HEGRA (power law, index 2.62,
  2.83 × 10⁻¹¹ cm⁻² s⁻¹ TeV⁻¹ at 1 TeV). The sensitivity is a fraction of this flux, converted to
  E² dN/dE at the arithmetic mean of the bin edges (1.0266 TeV for the 0.79–1.26 TeV bin, not its
  logarithmic centre at 1 TeV).
- The direction cut (`ThetaCut`) and the gamma/hadron cut are optimised in each bin. The direction cut
  has a lower limit, which depends on the file: for 50 h at 20°, 0.048° for Prod6 South, 0.044° for
  Prod6 North, 0.055° and 0.048° for Prod5 South and North. Over all the files used here it ranges from
  0.044° to 0.11°, larger for shorter optimisation times and larger zenith angles. Above about 1 TeV
  the cut stays at this limit while the PSF keeps getting narrower.
- On/off with `alpha = 0.2`, 5σ (Li & Ma), at least 10 excess events, excess at least 5 % of the
  background. The log gives the on, off and excess counts at the sensitivity limit and which of the
  three criteria sets it.

The same file holds every quantity also as a function of the source offset, in six 1°-wide bins
(`DiffSens_offaxis`, `EffectiveArea..._offaxis`, `ThetaCut_offaxis`, ...). These are computed from
diffuse gamma rays. Bin 0 (0–1°) of these histograms is identical, to the precision of the file, to
the FITS IRFs: `EFFAREA` in its first offset bin equals `EffectiveAreaEtrueNoTheta2cut_offaxis` bin 0,
and the FITS `DIFFERENTIAL SENSITIVITY` in its first offset bin equals `DiffSens_offaxis` bin 0.
The effective area was checked on the Prod6 and Prod5 files, the sensitivity on the Prod6 files
only (Prod5 has no sensitivity HDU); South and North, 50 h. **The FITS files describe a source
somewhere between 0° and 1° from the camera centre, while `DiffSens` is for a source on the axis.**

### The gammapy calculation

`performance.sensitivity` ([Method](method.md#differential-sensitivity)) uses only the FITS IRFs. The
on region is a circle of the 68 % containment radius of the FITS PSF, and the signal is scaled by 0.68.
The background is the `BKG` value at the centre of each bin, times the bin width and the solid angle of
the on region. The excess is converted to a flux with a power law of index 2.62, and E² dN/dE is given
at the arithmetic mean of the bin edges. The criteria are those of the official calculation (5σ,
10 events, 5 %, `alpha = 0.2`).

### Causes of the gap

The statistics are not one of them. Given the on and off counts printed in `IRFLog`, gammapy's
`WStatCountsStatistic` returns the same 5σ excess as the official calculation, to within 0.5 %.

Five causes were found. Two of them (2 and 4) are corrected in `performance.sensitivity`. The other
three cannot be corrected from the FITS files alone.

| Cause | Effect on the gammapy / official ratio | Corrected |
|---|---|---|
| 1. Source on axis (official) vs 0–1° (FITS) | +3–4 % median for Prod6, < 1 % for Prod5 | no, it is in the data |
| 2. Spectrum used to convert counts to flux | +2–3 % median | yes |
| 3. On region: 68 % PSF radius vs optimised cut | +20–50 % above 10 TeV; −15 to −45 % below 0.04 TeV | no, needs the ROOT cut |
| 4. Background integration near the threshold | down to 0.3 below 0.1 TeV | yes |
| 5. Empty PSF above 79 TeV (Prod6 North) | sensitivity not defined | no, it is in the data |

They were measured by changing the gammapy calculation one step at a time and comparing it with both
official curves: `DiffSens` (on axis) and `DiffSens_offaxis` bin 0 (0–1°, the one the FITS files
describe). Median ratios *gammapy / official* over 0.1–50 TeV, 50 h, zenith 20°:

| Calculation | Prod6 South | Prod6 North | Prod5 South | Prod5 North |
|---|---|---|---|---|
| E⁻² spectrum, log-log background (before correction), vs on axis | 1.11 | 1.08 | 1.09 | 1.11 |
| same, vs 0–1° | 1.07 | 1.05 | 1.09 | 1.09 |
| `performance.sensitivity` (causes 2 and 4 corrected), vs on axis | 1.08 | 1.06 | 1.06 | 1.05 |
| same, vs 0–1° | 1.03 | 1.02 | 1.05 | 1.04 |
| + official 0–1° cut radius and signal fraction, vs 0–1° | 1.02 | 1.01 | 1.01 | 1.01 |

Above 50 TeV, against the 0–1° curve, the last step brings the median ratio from 1.17 to 1.00 for
Prod6 South, from 1.35 to 1.01 for Prod5 South and from 1.44 to 1.07 for Prod5 North. Prod6 North is
treated [below](#5-no-psf-above-79-tev-for-prod6-north).

The last step uses `ThetaCut_offaxis` and the ratio `EffectiveArea_offaxis /
EffectiveAreaNoTheta2cut_offaxis` from the ROOT file. The FITS files do not contain them, so this step
cannot be reproduced from the FITS files alone. The remaining 1–2 % is of the size of the bin-to-bin
scatter between the two calculations; its origin was not looked for.

#### 1. Position of the source

`DiffSens` is for a source on the camera axis. The FITS IRFs, and therefore the gammapy curve, are for
the 0–1° offset bin. Over 0.1–50 TeV, the official 0–1° sensitivity is worse than the on-axis one by
3 % (Prod6 South) and 4 % (Prod6 North) in the median, and by up to 9 % in some bins. For Prod5 the
difference is below 1 % in the median. The effective area shows the same effect: the on-axis area is 2–5 %
larger than the 0–1° one.

This is also why the FITS `DIFFERENTIAL SENSITIVITY` HDU does not agree with `DiffSens`: they are not
for the same source position. For this reason the main validation figures,
`sensitivity-validation-<site>` and `sensitivity-ratio-<site>`, compare the gammapy curve with the
official sensitivity in the offset bin of the source (`DiffSens_offaxis`, or the FITS HDU when the
ROOT file is missing). The comparison with the on-axis `DiffSens`, the curve of the CTAO figures, is
kept in `sensitivity-validation-onaxis-<site>` and `sensitivity-ratio-onaxis-<site>`.

#### 2. Spectrum used to convert counts to flux

*Corrected.* gammapy's `SensitivityEstimator` converts the excess into a flux with an E⁻² spectrum by
default and quotes E² dN/dE at the logarithmic bin centre. The official calculation uses E⁻²·⁶² and the
arithmetic mean of the bin edges. Before the correction this accounted for 2–3 % of the median ratio.
The effect comes from the shape of the spectrum inside the 0.2-dex bin, from the events that migrate
into the bin from lower true energies (more numerous for a steeper spectrum), and from the energy at
which E² dN/dE is quoted: for an E⁻²·⁶² spectrum, moving from the centre to the arithmetic mean lowers
E² dN/dE by 1.6 %.

The index is `spectral_index` in the [sensitivity criteria](../how-to/change-sensitivity-criteria.md)
(default 2.62).

#### 3. On region and direction cut

*Not corrected.* gammapy uses the 68 % containment radius of a Gaussian PSF. The official cut is
optimised per bin and does not keep 68 % of the signal:

- Between 0.1 and 2 TeV, the official cut is 3–17 % smaller than the gammapy radius and keeps 61–68 %
  of the gamma rays. The gammapy on region then holds 10–45 % more background and up to 10 % more
  signal. The two effects largely cancel.
- At higher energies the official cut stays at its lower limit (see above), which is wider than the
  68 % radius of the PSF. It keeps up to 94 % of the gamma rays, against 68 % in the gammapy
  calculation. In these bins the background is small and the sensitivity is limited by the 10-event
  criterion, so it scales with the inverse of the signal fraction. This gives ratios of 1.2–1.5 above
  10 TeV, for example the Prod5 ratio of 1.4 above 50 TeV.
- Below about 0.04 TeV the official cut is wider than the gammapy radius (0.25–0.31° against 0.19–0.27°
  in the 0.02–0.03 TeV bin). These bins are limited by the 5 % background criterion, where the sensitivity
  is proportional to the background-to-signal ratio, so the smaller gammapy region gives a better
  sensitivity: ratios of 0.55–0.85 in the first bins.

In the 0.1–50 TeV median, the official cut changes the ratio by 1–2 % for Prod6 and by 3–4 % for Prod5,
mostly through the bins above a few TeV.

The cut limit varies from file to file (0.044° to 0.11°) and is not stored in the FITS files, so it
cannot be set from them. A cut optimised by gammapy itself would not reproduce it either: where the
background is close to zero, the optimum radius keeps growing.

The 68 % radius itself is close to the official one: the Gaussian radius agrees with `AngRes` to within
3 % in most bins between 0.04 and 50 TeV, and to within 10 % in all of them. The Gaussian approximation
of the PSF is not a significant cause.

#### 4. Background near the energy threshold

*Corrected.* gammapy's `SpectrumDatasetMaker` integrates the `BKG` rate over each bin of reconstructed
energy, interpolating log-log between bin centres. Near the threshold the rate jumps by an order of
magnitude from one bin to the next (Prod6 South at 0.5°: 0.016, 0.43 and 0.22 s⁻¹ MeV⁻¹ sr⁻¹ in the
first three bins). The interpolated integral over the 0.02–0.03 TeV bin is then 0.42 (Prod6 South),
0.50 (Prod6 North) and 0.39 (Prod5 North) times the tabulated value. For Prod5 South the factor is
0.12, 0.78, 0.67 and 0.80 in the bins from 0.02 to 0.13 TeV. These bins are limited by the 5 %
background criterion, so the sensitivity was too low by the same factor (ratios down to 0.3).
Between 0.1 and 50 TeV the interpolation multiplied the background by 0.72 to 1.50 depending on the
bin and the file.

The FITS `BKG` values themselves agree with `BGRatePerSqDeg_offaxis` bin 0 to within 1 % (2.5 % in one
bin). `performance.sensitivity` now uses the value at the bin centre times the bin width, as the
[background rate figure](#background-rate) and the official histograms do. The ratios left below
0.1 TeV (0.55–0.85) come from cause 3.

The figures hide the bins below the lowest energy of the official figures (`e_min_tev` in the release
YAML).

#### 5. No PSF above 79 TeV for Prod6 North

*Not corrected.* In the Prod6 North file the PSF of the 0–1° offset bin is empty above 79 TeV
(`SIGMA_1` and `SCALE` are 0), and so is `AngResEtrue_offaxis` bin 0. gammapy does not return a
zero radius there: it gives half its grid step (0.0002°) in the empty bins, and between the centre of
the last filled bin (63 TeV) and that of the first empty one (100 TeV) it interpolates the parameters
towards 0, which gives radii of 0.36–0.66°. Without a check, the 10-event criterion then gives a finite
but meaningless sensitivity. `performance.psf_filled` marks the energies between the first and last
filled bin centres; `performance.sensitivity` and `performance.angular_resolution` return NaN outside
them. The on-axis `DiffSens` has values there.

### Remaining approximations

These were not measured separately; their combined effect is within the residual 1–2 % above.

- *The background is assumed flat inside the on region*: it is read at the source position. The cube
  has 0.2° pixels.
- *The PSF radius is taken at the centre of the reconstructed-energy bin*, as if it were a true energy.
- *The IRFs are read at 0.5°*, which in the FITS tables is the 0–1° bin (gammapy interpolates
  between bin centres).

The `PSF_TABLE` HDU of the Prod6 files (tabulated PSF) is not used. gammapy 2.1 does not read it
with `PSF3D.read`: the axis order of `RPSF` does not match the one the class expects.

## Angular resolution

**Official.** `AngResEtrue`: 68 % containment radius vs true energy, from the full PSF distribution,
on axis.

**gammapy.** 68 % containment radius of the Gaussian from `SIGMA_1` and `SCALE`, at 0.5° (the 0–1°
bin), on a continuous energy grid. It is not binned, so it is compared with the ROOT bins at their
centres.

**Approximations.** Gaussian instead of the full distribution, and 0–1° instead of on axis. The official
0–1° radius differs from the on-axis one by up to 5 % in the median. Between 0.02 and 40 TeV the gammapy
radius agrees with `AngResEtrue` within 13 % (North) and 7 % (South). For Prod6 North the FITS PSF is
empty above 79 TeV ([cause 5](#5-no-psf-above-79-tev-for-prod6-north)), so the gammapy curve stops at
63 TeV, the centre of the last filled bin. The same check removes the energies below the centre of the
first filled bin (0.016 TeV for Prod6, 0.025 TeV for Prod5 South, whose first bin is empty), where
gammapy would otherwise extrapolate.

## Energy resolution

**Official.** `ERes`, drawn in the official figure as the "ΔE/E (68 % containment)" against true energy.
The histogram's own label says "RMS" ([ROOT files](../data/root-files.md#points-to-know)). For the
energy resolution, `IRFLog` prints "use median of energy distributions".

**gammapy.** For each true energy, the migration matrix gives the distribution of E_R/E_T at 0.5°. Each
true energy is weighted by `A_eff(E_T) × E_T^-2.62 × ΔE_T`; the weighted values falling in each bin of
true energy (for Prod6) give the 68 % half-width of |E_R/E_T − 1|.

**Approximations.** The weight assumes an E^-2.62 spectrum, the release one. The width is taken around 1,
not around the median. In the first and last bins, where the distribution is skewed, the choice of
centre and definition (68 % half-width or RMS) changes the result by tens of percent. The ROOT file
holds migration matrices with and without the direction cut (`MigMatrix`, `MigMatrixNoTheta2cut`);
which one the FITS matrix corresponds to has not been checked. The 0–1° `ERes` differs from the on-axis
one by 1–5 % in the median.

## Background rate

**Official.** `BGRatePerSqDeg`, per bin of reconstructed energy.

**gammapy.** `BKG` evaluated at 0.5° along DETY = 0, multiplied by the bin width (the cube is a rate
density per MeV and sr) and converted to Hz deg⁻². It agrees with `BGRatePerSqDeg_offaxis` bin 0
to within 1 % and with the on-axis `BGRatePerSqDeg` to within 8 % over 0.1–50 TeV. The value is taken at the bin centre,
not integrated over the bin; this matches how the ROOT histogram is filled.

## Effective area

**Official.** `EffectiveAreaNoTheta2cut` is the one comparable with the FITS (no direction cut).
`EffectiveArea` (with the direction cut) has no FITS equivalent: it is about 1.35–1.45 times lower.

**gammapy.** `EFFAREA` read at 0.5° on its own 42-bin energy axis. It is identical to
`EffectiveAreaEtrueNoTheta2cut_offaxis` bin 0 (0–1°). The on-axis ROOT area is 2–5 % higher in the
median, with individual bins between 0.78 and 1.08 times the ROOT value (0.1–50 TeV). The difference
is the one between a source on axis and a source in the 0–1° bin
([cause 1](#1-position-of-the-source)).

## Other curves

- *Off-axis sensitivity.* Computed at offsets from 0.5° to 4.5°, every 0.25°, with gammapy
  interpolating linearly between the 1° bin centres. The ROOT version has one value per 1° bin.
- *Sensitivity vs time (Prod5 short-term figure, Prod6 `sensitivity-time`).* Computed with gammapy for
  other livetimes than the optimisation time, using the cuts optimised for another duration. An analysis
  optimised for each livetime would give a different result. No ROOT equivalent.

## How the gap was measured

All numbers on this page come from the release files. The official per-bin counts are in the `IRFLog`
object of each ROOT file, in the first block headed "calculating or reading differential sensitivity":
for each bin, the `CU RESULTS` line gives the on, off and excess counts for one Crab unit, and the
`SENS RESULTS` line the counts at the sensitivity limit. The 0–1° quantities are bin 0 of the
`*_offaxis` histograms. The gammapy side uses `performance.sensitivity` and the same dataset with the
changes listed in [Causes of the gap](#causes-of-the-gap).

## Limitation of a FITS-only calculation

The gammapy sensitivity is computed from the FITS IRFs only. With this constraint, three of the five
causes above cannot be corrected:

- **The direction cut (cause 3).** The FITS IRFs are `FULL-ENCLOSURE`: they have the gamma/hadron cut
  but no direction cut, and they do not record the cut used for the official sensitivity
  (`ThetaCut` in the ROOT file). The gammapy calculation replaces it with the 68 % containment radius
  of the PSF. The official cut has a lower limit, between 0.044° and 0.11° depending on the file, that
  cannot be derived from the FITS tables. As a result, above about 10 TeV the gammapy sensitivity is up to
  40 % worse than the official 0–1° curve (up to 50 % worse than the on-axis one), and below about
  0.04 TeV it is 15–45 % better. With the ROOT cut, the
  median ratio to the 0–1° official curve would fall from 1.02–1.05 to 1.01–1.02, and the ratio above
  50 TeV to 1.00–1.07.
- **The source position (cause 1).** The FITS IRFs are for a source 0–1° from the camera centre. The
  on-axis official curve cannot be reproduced from them; it is 0–9 % better per bin.
- **The empty PSF of Prod6 North above 79 TeV (cause 5).**

Use the gammapy curves above 10 TeV and below 0.04 TeV with this in mind.

## What to do if you need the official numbers

Use the ROOT curves ([Reproduce the figures from ROOT](../how-to/reproduce-figures-from-root.md)):
the site shows them with each figure, with an ASCII file. The CTAO performance page is the reference:
<https://www.ctao.org/for-scientists/performance/>.

For a source off axis, the `DiffSens_offaxis` histogram, or the `DIFFERENTIAL SENSITIVITY` HDU of the
Prod6 FITS files, is the official reference. It is the one the FITS IRFs, and the gammapy curves,
correspond to.

The gammapy figures are for understanding and for studies where the criteria need to change
(significance, number of off regions, energy binning, livetime, offset). They are not official CTAO products.
