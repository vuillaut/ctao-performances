# Read the FITS files directly, without gammapy

Every IRF is a one-row binary table: columns hold the axes and the data cube.
Use the HDU name, not its index (Prod5 and Prod6 have different HDU orders).

```python
import numpy as np
from astropy.io import fits

path = "data/prod6-v1.0/irfs/Prod6-CTAO-South-20deg-AverageAz-2LSTs14MSTs37SSTs-dark-180000s-v1.0.fits.gz"
with fits.open(path) as hdul:
    row = hdul["EFFECTIVE AREA"].data[0]
    e_lo, e_hi = row["ENERG_LO"], row["ENERG_HI"]       # TeV, 42 bins
    aeff = row["EFFAREA"]                                # m2, shape (6, 42) = (theta, energy)

e_center = np.sqrt(e_lo * e_hi)
print(aeff[0, np.argmin(abs(e_center - 1))])             # offset 0-1 deg, ~1 TeV
```

The array shape is reversed with respect to the FITS `TDIM` (`(42,6)`) because
FITS stores the first axis fastest: in NumPy, the **last** axis is energy for
`EFFAREA`. The energy dispersion is the case to watch: its `TDIM` is
`(300,300,6)` = (energy, migra, theta), so in NumPy the energy axis is last and
the migration axis is in the middle. Quick reference:

| HDU | Quantity | numpy shape | Axes (slowest → fastest) |
|---|---|---|---|
| `EFFECTIVE AREA` | `EFFAREA` | (6, 42) | theta, energy_true |
| `POINT SPREAD FUNCTION` | `SIGMA_1`, `SCALE`, ... | (6, 21) | theta, energy_true |
| `ENERGY DISPERSION` | `MATRIX` | (6, 300, 300) | theta, migra, energy_true |
| `BACKGROUND` | `BKG` | (60, 60, 21) | dety, detx, energy (GADF order; both axes have identical edges, so check `TDIM`) |
| `DIFFERENTIAL SENSITIVITY` (Prod6) | `DIFFSENS` | (6, 21) | theta, energy |

Check this against `TDIM` of your file before trusting it. Where each value
sits and what it means: [FITS contents](../data/fits-contents.md).

## Find an HDU by class instead of name

```python
def find(hdul, hduclas4):
    return next(h for h in hdul[1:] if h.header.get("HDUCLAS4") == hduclas4)

sens = find(hdul, "DIFFSENS_2D")
```

This is what `irfs.py` does for the tabulated sensitivity.

## Units

Read them from the header rather than assuming: `hdul[...].columns["EFFAREA"].unit`
gives `m**2`; pass it to `astropy.units.Unit`. The background is in
s⁻¹ MeV⁻¹ sr⁻¹ — per MeV, although the energy axis is in TeV.
