# GADF compliance

**Short answer: yes, with documented deviations.** The IRF HDUs follow the
[Data formats for gamma-ray astronomy](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/)
(GADF) full-enclosure IRF specification, so gammapy loads them (no other reader
was tested). Read the GADF pages for the definition of each IRF; this
page only lists what is specific to the CTAO files. The Prod6 Zenodo README says: "FITS products are
compatible with the Gamma-ray Astronomy Data Formats (GADF) specification".

The files were compared against the v0.3 pages for `AEFF_2D`, `EDISP_2D`,
`PSF_3GAUSS`, `PSF_TABLE` and `BKG_3D`, and checked all 354 files for the
header keywords. This is a reading of the spec, not a run of a formal validator.

## Where to read the spec

| IRF here | GADF page |
|---|---|
| Effective area, `AEFF_2D` | [Effective area](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/irfs/full_enclosure/aeff/index.html) |
| Energy dispersion, `EDISP_2D` | [Energy dispersion](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/irfs/full_enclosure/edisp/index.html) |
| PSF, `PSF_3GAUSS` | [PSF 3-Gauss](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/irfs/full_enclosure/psf/psf_3gauss/index.html) |
| PSF, `PSF_TABLE` | [PSF table](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/irfs/full_enclosure/psf/psf_table/index.html) |
| Background, `BKG_3D` | [Background](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/irfs/full_enclosure/bkg/index.html) |
| General | [IRF overview](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/irfs/index.html), [full-enclosure IRFs](https://gamma-astro-data-formats.readthedocs.io/en/v0.3/irfs/full_enclosure/index.html) |

## What matches

- `HDUCLASS=GADF`, the `HDUDOC` URL, `HDUCLAS1=RESPONSE`, `HDUCLAS2` (`EFF_AREA`,
  `EDISP`, `PSF`, `BKG`), `HDUCLAS3=FULL-ENCLOSURE`, `HDUCLAS4` (`AEFF_2D`, `EDISP_2D`,
  `PSF_3GAUSS`, `PSF_TABLE`, `BKG_3D`) on every IRF HDU.
- All required columns are present, with the units the spec gives (TeV, deg, m²,
  sr⁻¹, s⁻¹ MeV⁻¹ sr⁻¹), one row per HDU, axes as `*_LO`/`*_HI` pairs.
- The recommended `EXTNAME`s are used: `EFFECTIVE AREA`, `ENERGY DISPERSION`,
  `POINT SPREAD FUNCTION`, `BACKGROUND`.
- Axis order is the recommended one for `AEFF_2D` (energy, theta), `EDISP_2D`
  (energy, migra, theta), `PSF_3GAUSS` (energy, theta) and `BKG_3D` (energy, detx,
  dety).
- `BKG_3D` carries the `FOVALIGN` keyword (`RADEC`).

## Deviations

| # | What | Impact |
|---|---|---|
| 1 | `HDUVERS = 0.2` in every IRF HDU; the v0.3 pages ask for `0.3`. | Cosmetic for gammapy, which reads these files. A strict validator would flag it. |
| 2 | `DIFFERENTIAL SENSITIVITY` HDU (`HDUCLAS4=DIFFSENS_2D`, Prod6 only) is not one of the five IRF components on the v0.3 full-enclosure page, and has no `HDUCLAS2`. | Readers that follow GADF ignore it. This repository reads it with `irfs.provided_sensitivity`. |
| 3 | `EFFAREA_ERR` extra column in `EFFECTIVE AREA` (Prod6 only). | Ignored by readers that do not know it. |
| 4 | `PSF_3GAUSS` holds a single Gaussian: `SIGMA_2`, `SIGMA_3`, `AMPL_2`, `AMPL_3` are all zero. | Valid; the spec says zero amplitudes give a single or double Gaussian. Only the PSF is approximated, as the release notes state. |
| 5 | `PSF_TABLE` (Prod6 only) is stored as (energy, rad, theta); the spec recommends (energy, theta, rad). | Axis order is a recommendation. This repository does not use that HDU. |
| 6 | No `obs-index` / `hdu-index` files. Each file is a standalone IRF. | Index files are not required for IRFs, per the spec, but tools that expect a CALDB or a data store cannot discover these files. Here the file name encodes the selection ([File naming](file-naming.md)). |
| 7 | Optional `LO_THRES`/`HI_THRES` keywords are absent. | The energy threshold is not in the file. |
| 8 | Unit strings are written `m**2`, `sr^(-1)`, `s^-1 MeV^-1 sr^-1`, `erg cm^-2 s^-1`, spelled in several styles. | astropy parses them all. |
| 9 | Primary header `TELESCOP` differs from the IRF HDUs (`CTA (MC prod5, v0.1.1)` in Prod6 files, which are labelled prod5), and `INSTRUME` differs between Prod5 (`Southern Array`) and Prod6 (`CTAO Southern Array`). | Cosmetic; do not use these keywords to identify the release. Use the file name and the DOI. |

## Using the files with other tools

Because the files are standalone, point the tool at the file rather than at a
data store. With gammapy:

```python
from gammapy.irf import load_irf_dict_from_file
irfs = load_irf_dict_from_file(path)        # keys: aeff, edisp, psf, bkg
```

This is what `ctao_perf.irfs` does, plus the energy-dispersion patch described in
[FITS contents](fits-contents.md#known-data-issues).

## Not covered by GADF here

The ROOT files of each release are not GADF. They keep the full PSF and hold additional
histograms such as the sensitivity and the energy and angular resolution curves. See
[ROOT files](root-files.md).
