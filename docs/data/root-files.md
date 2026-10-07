# ROOT files

Besides the FITS IRFs, each release ships the **ROOT files** produced by the CTAO analysis
(Eventdisplay). They hold the histograms behind the official performance figures, so they are
the reference to compare with. `ctao-perf` reads them with [uproot](https://uproot.readthedocs.io),
in pure Python: no ROOT installation is needed.

Checked on the Prod6 v1.0 and Prod5 v0.1 files: both have the same histograms, with the same names and
binning.

## Getting them

```bash
ctao-perf download --root prod6-v1.0
```

The ROOT files are in a separate Zenodo bundle: about 1.1 GB for Prod6 (`ctao-prod6-zenodo-v1.0.zip`),
0.9 GB for Prod5 (`cta-prod5-zenodo-v0.1.zip`). The tool reads the tarballs inside the zip and keeps only
the files the figures use: default azimuth (`AverageAz`) and sky condition (`dark`), the full array of
every site, every zenith angle and optimisation time. That is 32 files, about 205 MB, for Prod6 and 18
files, about 137 MB, for Prod5, in `data/<release>/root/`. The zip is deleted afterwards. `.root_unpacked`
marks a finished unpack. In Prod5 the tarballs also hold the sub-array files (LSTs only, MSTs only, ...);
they are not extracted.

File names are those of the FITS files with `.root` instead of `.fits.gz`
([File naming](file-naming.md)). Use `Release.root_irf_filename(...)` or `RootLibrary.path(...)`.

A bundle in the Zenodo record has 12 ROOT files per (site, zenith, sky) tarball: 3 azimuths × 4
durations.

## Histograms

All the histograms of one file (one site, zenith, azimuth, sky, optimisation time):

| Histogram | Type | Content | Used here |
|---|---|---|---|
| `DiffSens`, `DiffSensCU` | `TH1F` | differential sensitivity, in erg cm⁻² s⁻¹ and in Crab units | `DiffSens` |
| `IntSens`, `IntSensCU` | `TH1F` | integral sensitivity | |
| `BGRate`, `ProtRate`, `ElecRate` | `TH1F` | residual background rate: total, protons, electrons (Hz) | |
| `BGRatePerSqDeg`, `ProtRateSqDeg`, `ElecRateSqDeg` | `TH1F` | same, per square degree | `BGRatePerSqDeg` |
| `EffectiveArea`, `EffectiveAreaEtrue` | `TH1F` | effective area with the direction cut, vs reconstructed or true energy | `EffectiveArea` |
| `EffectiveAreaNoTheta2cut`, `...EtrueNoTheta2cut` | `TH1F` | same without direction cut | `EffectiveAreaNoTheta2cut` |
| `EffectiveArea80` | `TH1F` | effective area for a cut keeping 80 % of gamma rays | |
| `AngRes`, `AngResEtrue` (+`80`, `95`) | `TH1F` | angular containment radius (68, 80, 95 %) vs reconstructed or true energy | `AngResEtrue` |
| `ERes`, `Ebias` | `TH1F` | energy resolution and bias | `ERes` |
| `Theta2Cut`, `ThetaCut` | `TH1F` | direction cut applied in each energy bin | |
| `MigMatrix`, `MigMatrixNoTheta2cut`, `EestOverEtrue`, `EestOverEtrueNoTheta2cut` | `TH2D` | energy migration | |
| `AngularPSF2D`, `AngularPSF2DEtrue` | `TH2D` | full PSF | |
| `*_offaxis` | `TH2F`, `TH3F` | the same, binned in angle from the camera centre (6 bins of 1°) | `DiffSens_offaxis` |
| `debug/DiffSens_*` | `TH1F` | significance, event numbers and which criterion limited the sensitivity | |
| `telconfig`, `IRFLog` | `TTree`, `TMacro` | telescope configuration; log of the production | |

Binning of the energy axis: `log10(E/TeV)` from −1.9 to 2.3. The 1-D histograms have 21 bins
(five per decade), except the effective area which has 42. The histograms carry titles and axis
labels, for instance `DiffSens`: "E^{2} dF/dE [erg cm^{-2} s^{-1}]".

The energy axis is labelled `log_{10} (E/TeV)` in most histograms, `log_{10} (E_{Rec}/TeV)` in
`AngRes` and `log_{10} (E_{MC}/TeV)` in `AngResEtrue`. The files do not say more; the names (`Etrue`)
and the official figures indicate that the angular resolution, energy resolution and effective
area are drawn against true energy, the sensitivity and the background against reconstructed energy.

## Reading them

```python
import uproot, numpy as np
f = uproot.open("data/prod6-v1.0/root/Prod6-CTAO-South-20deg-AverageAz-2LSTs14MSTs37SSTs-dark-180000s-v1.0.root")
values, log_edges = f["DiffSens"].to_numpy()
edges_tev = 10 ** log_edges            # 22 edges
values[values <= 0] = np.nan           # zero means "no value"
```

`ctao_perf.root` wraps this: `differential_sensitivity(path)`, `angular_resolution(path)`,
`energy_resolution(path)`, `effective_area(path, direction_cut=False)`, `background_rate(path)`,
`differential_sensitivity_offaxis(path)`. Each returns a `Curve` (or arrays for the off-axis map)
with energies in TeV.

## Points to know

- **`ERes` is labelled "RMS"** on its y axis. The official figure labels the same numbers
  "ΔE/E (68 % Containment)". The values in the file are identical to the ones plotted in the official
  figure (for example 0.273 for the South array in the bin around 0.025 TeV), so `ctao-perf` treats them
  as the 68 % half-width and labels the figure accordingly. The file does not say more.
- **Zero means no value.** Empty bins are 0 in the file; `ctao_perf.root` turns them to NaN.
- **The main histograms are on axis, the FITS IRFs are for 0–1°.** `DiffSens`, `EffectiveArea...`,
  `AngRes...` and the others without suffix are computed from gamma rays simulated as a point source on
  the camera axis (`gamma_onSource` in `IRFLog`). The FITS IRFs equal bin 0 (0–1°) of the `*_offaxis`
  histograms, computed from diffuse gamma rays: `EFFAREA` equals `EffectiveAreaEtrueNoTheta2cut_offaxis`
  bin 0 (checked on the Prod6 and Prod5 50 h files, both sites), and the FITS `DIFFERENTIAL
  SENSITIVITY` equals `DiffSens_offaxis` bin 0 (Prod6 50 h files, both sites; Prod5 has no such HDU). Between the two, the sensitivity differs by up to 9 % per bin
  (3–4 % in the median for Prod6) and the effective area by 2–5 % in the median. See
  [Differences from the official figures](../explanation/differences-from-official.md#1-position-of-the-source).
- **`EffectiveArea` has a direction cut, the FITS does not.** All FITS IRFs are `FULL-ENCLOSURE`.
  `EffectiveArea` is 1.35 to 1.45 times lower than the FITS area between 0.1 and 50 TeV (median).
- **`IRFLog` records the sensitivity calculation.** For each energy bin it gives the on, off and
  excess counts for one Crab unit (`CU RESULTS`) and at the sensitivity limit (`SENS RESULTS`),
  `alpha`, the spectrum used (HEGRA Crab, index 2.62) and which criterion sets the limit. The first block
  headed "calculating or reading differential sensitivity" is the one for `DiffSens`; later blocks are
  for the integral and the off-axis sensitivities.
- **Off-axis**: all six 1° bins of `DiffSens_offaxis` are filled in the Prod6 South file, whereas the
  `DIFFERENTIAL SENSITIVITY` HDU of the FITS file is non-zero for the first three only.
- **Not GADF.** The ROOT format is specific to Eventdisplay. See [GADF compliance](gadf-compliance.md).
