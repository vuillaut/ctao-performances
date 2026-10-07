# Figure catalogue

Producers in `figures.py`, in run order. "Per site" means one PNG per site, with the site key appended
to the id. Each figure is made for the sources listed: `gammapy` (recomputed from the FITS IRFs)
or `root` (official curves from the ROOT files), and saved as `<source>/<id>.png`, `.dat` and `.py`
([ASCII files](../how-to/use-the-ascii-files.md)).

| Producer | Figure id | Sources | Shows | ROOT histogram |
|---|---|---|---|---|
| `sensitivity_durations` | `sensitivity-durations-<site>` (per site) | gammapy, root | Differential sensitivity for each observation time, each with its own optimised IRF | `DiffSens` |
| `sensitivity_north_south` | `sensitivity-north-south` | gammapy, root | Both sites, reference duration | `DiffSens` |
| `sensitivity_zenith` | `sensitivity-zenith-<site>` (per site) | gammapy, root | Sensitivity vs zenith angle; skipped if fewer than two zeniths exist | `DiffSens` |
| `sensitivity_validation` | `sensitivity-validation-<site>`, `sensitivity-ratio-<site>` (per site) | gammapy | The gammapy sensitivity next to the official one for the same source offset bin (0–1° by default), and the ratio of the two. The official curve is `DiffSens_offaxis` from the ROOT file, or the FITS `DIFFERENTIAL SENSITIVITY` HDU when the ROOT file is missing | `DiffSens_offaxis` |
| `sensitivity_validation` | `sensitivity-validation-onaxis-<site>`, `sensitivity-ratio-onaxis-<site>` (per site) | gammapy | Same, against the on-axis official sensitivity of the CTAO figures (needs the ROOT file) | `DiffSens` |
| `offaxis_sensitivity` | `offaxis-sensitivity-<site>` (per site) | gammapy, root | Sensitivity vs FoV offset, relative to the first offset, for selected energy bands (needs `offaxis.bins_tev`) | `DiffSens_offaxis` |
| `sensitivity_vs_time` | `sensitivity-time-<site>` (per site) | gammapy | Sensitivity vs observation time (10 s–10⁴ s) at fixed energies (needs `short_term`) | none |
| `angular_resolution` | `angular-resolution` | gammapy, root | 68 % containment radius vs true energy | `AngResEtrue` |
| `energy_resolution` | `energy-resolution` | gammapy, root | 68 % half-width of ΔE/E | `ERes` |
| `effective_area` | `effective-area-<site>` (per site) | gammapy, root | Effective area for each duration, no direction cut | `EffectiveAreaNoTheta2cut` |
| `effective_area_direction_cuts` | `effective-area-direction-cuts-<site>` (per site) | root | Effective area with the optimised direction cut | `EffectiveArea` |
| `background_rate` | `background-rate` | gammapy, root | Residual background in Hz deg⁻² | `BGRatePerSqDeg` |

On the website, figures of the same id are shown side by side, with the official PNG when the release
YAML maps it (`reference_figures`). Method and approximations:
[Method](../explanation/method.md), [Differences](../explanation/differences-from-official.md).
