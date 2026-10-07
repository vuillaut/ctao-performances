# Method

All quantities come from the FITS IRFs of one file. Nothing is simulated.

## Differential sensitivity

`performance.sensitivity` builds a one-observation spectrum dataset and hands it
to `gammapy.estimators.SensitivityEstimator`.

1. **Geometry.** Pointing at (0°, 0°) ICRS, source `offset` (0.5°) away. Reconstructed
   energy axis: 5 bins per decade from 10^-1.9 to 10^2.3 TeV (21 bins). True-energy
   axis: 25 bins per decade, 0.005–500 TeV.
2. **Exposure and energy dispersion** come from `SpectrumDatasetMaker`
   applied to an `Observation` with the IRFs and the livetime. The livetime is in
   general the optimisation time of the file, but it can differ (sensitivity vs
   time).
3. **On region = 68 % containment.** In each energy bin, the on-region radius is the
   68 % PSF containment radius at that energy and offset. The exposure is
   multiplied by 0.68.
4. **Background** is the `BKG` rate at the source offset and at the centre of each
   reconstructed-energy bin, times the bin width, the solid angle of the on region
   `2π (1 − cos r)` and the livetime. It is not taken from `SpectrumDatasetMaker`,
   whose log-log integration underestimates the background near the threshold.
5. **Off regions.** `acceptance_off = 1/alpha = 5`: five times the on exposure.
6. **Detection criteria** (`SensitivityCriteria`): 5σ (Li & Ma), at least 10 excess
   events, excess at least 5 % of the background.
7. **Output** is E² dN/dE in erg cm⁻² s⁻¹ for a power law of index 2.62
   (`spectral_index`) in each bin, at the arithmetic mean of the bin edges, as in the
   official curves. Bins with a non-finite or non-positive result become NaN.

Only the FITS file is used. The official analysis optimises the direction cut in each
bin, and this cut is not stored in the FITS files, so step 3 replaces it with a fixed
containment fraction. These steps contain approximations; each is listed, with the measured effect, in
[Why the gammapy figures differ from the official ones](differences-from-official.md).

## Angular resolution

68 % containment radius of the PSF (`PSF_3GAUSS`) as a function of **true**
energy at the source offset.

## Energy resolution

Half-width of the interval centred on 0 that contains 68 % of the distribution of
(E_R − E_T)/E_T. For each true energy, the migration matrix gives the
distribution of μ = E_R/E_T (oversampled on 1801 points from 0.2 to 2.0). Each true
energy is weighted by A_eff(E_T) · E_T^−2.62 · ΔE_T, as for an E^-2.62 source
spectrum, and the weighted values falling in each bin are used to compute the
68 % half-width. The bin is on reconstructed or true energy according to
`energy_resolution_axis`.

## Effective area and background

Both are read at the offset and shown on their native binning. The background
rate is the `BKG` value (a rate density per MeV and sr) evaluated at the offset,
multiplied by the width of each reconstructed-energy bin and converted to Hz deg⁻². The effective area is the
one after gamma/hadron cuts and with no cut on the reconstructed direction (the
HDUs are `FULL-ENCLOSURE`).

## Off-axis and short-term sensitivity

The off-axis figure repeats the sensitivity at offsets from 0.5° to 4.5° in
0.25° steps and divides by the 0.5° value, in the bin nearest the centre of each
requested energy band. The IRFs have 1°-wide offset bins, so gammapy
interpolates linearly between bin centres.

The short-term figure uses a single reconstructed-energy bin of ±0.1 dex around
each requested energy, for livetimes from 10 s to 10⁴ s, always with the IRF
optimised for `short_term.duration`.
