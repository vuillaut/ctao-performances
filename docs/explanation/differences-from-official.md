# Why the gammapy figures differ from the official ones

Our gammapy curves are not the official ones. This page says, curve by curve, what is computed,
what is approximated and how large the gap is. The gaps are measured against the official curves in
the ROOT files, for Prod6 v1.0 (South and North, 50 h, zenith 20°, `AverageAz`, dark sky). Prod5 has
no ROOT comparison yet.

Ratios are *gammapy / official*, over 0.1–50 TeV, the range where the analysis has good statistics
([ratio figures](../reference/figures.md)). "Median" is the median over the energy bins.

| Curve | What we compute | Median ratio (North / South) | Range | Where it gets worse |
|---|---|---|---|---|
| Differential sensitivity | gammapy `SensitivityEstimator` on an on/off dataset built from the FITS IRFs | 1.08 / 1.11 | 1.05–1.19 / 1.03–1.32 | below 0.05 TeV, above 50 TeV |
| Angular resolution | 68 % containment radius of the Gaussian PSF | 1.01 / 1.00 | 0.87–1.08 / 0.93–1.07 (0.02–40 TeV) | North above 60 TeV |
| Energy resolution | 68 % half-width of (E_R − E_T)/E_T from the migration matrix | 1.01 / 1.09 | 0.79–1.16 / 0.95–1.20 | first and last bins |
| Background rate | `BKG` cube integrated per bin, at 0.5° | 1.00 / 1.01 | 0.94–1.00 / 1.00–1.08 | |
| Effective area | `EFFAREA` at 0.5°, no direction cut | 0.96 / 0.98 | 0.78–1.07 / 0.88–1.08, vs the ROOT area without direction cut | |

A ratio above 1 on the sensitivity means ours is worse (a larger flux is needed). Our sensitivity is
about 10 % higher than the official one in the middle of the range, never lower there. This is
the figure that matters most; the details follow.

## Differential sensitivity

**Official.** `DiffSens` in the ROOT file: sensitivity of the full analysis, with the cuts (gamma/hadron
and direction) optimised for each energy bin and observation time.

**Ours.** `performance.sensitivity` ([Method](method.md#differential-sensitivity)). The inputs are the
FITS effective area, energy dispersion, background and PSF. The criteria are those of the release README
(5σ, ≥ 10 excess events, S/B ≥ 5 %, five bins per decade).

**Approximations.**

1. *No optimised direction cut.* The FITS IRFs are `FULL-ENCLOSURE`: gamma/hadron cuts are applied,
   the direction cut is not. We replace it by a fixed 68 % containment radius of the PSF, with the
   exposure scaled by 0.68. CTAO optimises the cut radius in each bin (`ThetaCut`, `Theta2Cut` in the
   ROOT file), so the fraction of signal kept is not 68 % in general; I did not compare the two radii.
   This is, I believe, the main reason our sensitivity is not the official one, but I have not
   isolated its effect.
2. *The PSF is a single Gaussian.* In the FITS files `SIGMA_2/3` and `AMPL_2/3` are zero. The 68 % radius
   from a Gaussian is close to the official one (table above) but the non-Gaussian tails, which matter
   for the background and the signal fraction, are lost.
3. *The PSF radius is taken at the centre of the reconstructed-energy bin*, as if it were a true energy.
   With a finite energy resolution the true energies in a bin are spread around it.
4. *The background is scaled by a ratio of solid angles*, from the 0.1° circle used to read the cube
   to the on region. That assumes a background that is flat inside the region. The cube has 0.2°
   pixels, which is coarse next to a 0.03° radius at high energy.
5. *The number of off regions is assumed*: `alpha = 0.2`, i.e. five times the on exposure. The release
   README does not state the value the official analysis uses.
6. *The spectrum of the estimator is the gammapy default*, not the E^-2.62 of the production. The effect
   is small in bins of 0.2 dex but not zero.
7. *The livetime is the optimisation time of the file*, and the IRF is read at 0.5°, in the first
   1°-wide offset bin of the FITS tables. I believe, without having checked, that the official numbers
   are on axis.

**Where it breaks.** Below about 0.05 TeV the ratio falls to 0.3 (South) and 0.02–0.3 (North) in the
first bins above the plotted threshold: the FITS IRFs are poor there (large migration, few events) and our
estimator gives a much better sensitivity than the official analysis. I did not find the cause.
Above 50 TeV the ratio is 1.0–1.5 with only three bins. The figures hide the bins below the lowest energy
of the official figures (`e_min_tev` in the release YAML), but the lowest plotted bin is already affected
for North.

**Against the FITS table.** The `DIFFERENTIAL SENSITIVITY` HDU of the FITS file is also in the validation
figure. It is within about 10 % of the ROOT `DiffSens`, and 29 % in the lowest bin, so the two
official sources do not match exactly either.

## Angular resolution

**Official.** `AngResEtrue`: 68 % containment radius vs true energy, from the full PSF distribution.

**Ours.** 68 % containment radius of the Gaussian from `SIGMA_1` and `SCALE`, at 0.5°, on a continuous
energy grid. It is not binned, so it is compared with the ROOT bins at their centres.

**Approximations.** Gaussian instead of the full distribution (point 2 above); the FITS tables are
averaged over the first 1° offset bin. Between 0.02 and 40 TeV it agrees within 13 % (North) and 7 % (South). At the highest
energies of the North array it breaks (a factor 1.7 and 5 at 63 and 100 TeV); I did not look into it.

## Energy resolution

**Official.** `ERes`, drawn in the official figure as the "ΔE/E (68 % containment)" against true energy.
The histogram's own label says "RMS" ([ROOT files](../data/root-files.md#points-to-know)).

**Ours.** For each true energy, the migration matrix gives the distribution of E_R/E_T at 0.5°. Each true
energy is weighted by `A_eff(E_T) × E_T^-2.62 × ΔE_T`; the weighted values falling in each bin of true
energy (for Prod6) give the 68 % half-width of |E_R/E_T − 1|.

**Approximations.** The weight assumes an E^-2.62 spectrum, the release one. The ROOT file also holds
migration matrices with and without the direction cut (`MigMatrix`, `MigMatrixNoTheta2cut`); which one the
FITS matrix corresponds to is not documented and I did not check. A different definition of the
width (68 % half-width around 0 versus around the median, versus RMS) changes the numbers by tens of
percent in the first and last bins, where the distribution is skewed.

## Background rate

**Official.** `BGRatePerSqDeg`, on axis, per bin of reconstructed energy.

**Ours.** `BKG` evaluated at 0.5° along DETY = 0, multiplied by the bin width (the cube is a rate density
per MeV and sr) and converted to Hz deg⁻². The agreement is within 10 % over the whole range. The
integration uses the value at the centre of the bin (no integration over the bin), a small effect in
five-bins-per-decade binning.

## Effective area

**Official.** `EffectiveAreaNoTheta2cut` is the one comparable with the FITS (no direction cut).
`EffectiveArea` (with the direction cut) has no FITS equivalent: it is about 1.35–1.45 times lower.

**Ours.** `EFFAREA` read at 0.5° on its own 42-bin energy axis. Its median is 2–4 % below the ROOT area, with
individual bins between 0.78 and 1.08 times the ROOT value (0.1–50 TeV). I do not know why; a likely cause, not checked, is the 1° offset
binning of the FITS.

## Other curves

- *Off-axis sensitivity.* Ours is computed at offsets from 0.5° to 4.5°, every 0.25°, and gammapy
  interpolates linearly between the 1° bin centres. The ROOT version has one value per 1° bin.
- *Sensitivity vs time (Prod5 short-term figure, Prod6 `sensitivity-time`).* Computed with gammapy for
  other livetimes than the optimisation time, using the cuts optimised for another duration, which is
  not what an analysis optimised for that time would give. No ROOT equivalent.

## What to do if you need the official numbers

Use the ROOT curves ([Reproduce the figures from ROOT](../how-to/reproduce-figures-from-root.md)):
the site shows them with each figure, with an ASCII file. The CTAO performance page is the reference:
<https://www.ctao.org/for-scientists/performance/>.

The gammapy figures are for understanding and for studies where you need to change the criteria
(significance, number of off regions, energy binning, livetime, offset). They are not official CTAO products.
