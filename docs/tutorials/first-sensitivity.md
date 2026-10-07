# Your first sensitivity

You will load one IRF file, compute the 50 h differential sensitivity of
CTAO-South and plot it. It assumes you finished
[Getting started](getting-started.md) and have `data/prod6-v1.0/`.

## 1. Load the release and the IRFs

```python
import astropy.units as u
from ctao_perf import load_release
from ctao_perf.irfs import IRFLibrary

release = load_release("prod6-v1.0")
library = IRFLibrary(release, "data")
irfs = library.load("South", 180000)      # 180000 s = the 50 h optimisation
print(sorted(irfs))
```

```
['aeff', 'bkg', 'edisp', 'psf']
```

`"South"` is a key of `release.sites`; `180000` is the optimisation time in
seconds, as encoded in the file name. Zenith, azimuth and sky condition default
to the values in the release YAML (20°, `AverageAz`, `dark`). Change them with
keywords:

```python
irfs40 = library.load("South", 180000, zenith=40, condition="halfmoon")
```

## 2. Compute the sensitivity

```python
from ctao_perf import performance as perf

axis, e2dnde, table = perf.sensitivity(
    irfs, livetime=50 * u.h, location="ctao_south"
)
for e, s in zip(axis.center, e2dnde):
    print(f"{e.value:8.3f} TeV  {s:.2e} erg cm-2 s-1")
```

`e2dnde` is a numpy array in erg cm⁻² s⁻¹, one value per reconstructed-energy
bin (five per decade between 10^-1.9 and 10^2.3 TeV). Bins where the estimator
fails are `nan`. `table` is the raw gammapy table.

## 3. Plot it

```python
import matplotlib.pyplot as plt

plt.loglog(axis.center, e2dnde, "o")
plt.xlabel("Reconstructed energy [TeV]")
plt.ylabel(r"E$^2$ dN/dE [erg cm$^{-2}$ s$^{-1}$]")
plt.savefig("my-sensitivity.png")
```

The minimum should sit near 10⁻¹³ erg cm⁻² s⁻¹ around 1–10 TeV.

## 4. Compare with the official value

Prod6 files ship the official sensitivity in the `DIFFERENTIAL SENSITIVITY`
HDU:

```python
e_edges, theta_edges, official = library.provided_sensitivity("South", 180000)
# official[theta_bin, energy_bin], erg cm-2 s-1; theta_bin 0 is 0-1 deg
```

Computing on the same energy edges makes the two comparable:

```python
from gammapy.maps import MapAxis
same_axis = MapAxis.from_energy_edges(e_edges, name="energy")
_, ours, _ = perf.sensitivity(irfs, 50 * u.h, "ctao_south", energy_axis=same_axis)
ratio = ours / official[0]
```

Expect ratios between 0.9 and 1.3 from 0.1 to 50 TeV, mostly 1.0–1.1 (this is what
`tests/test_performance.py` asserts). [Why they differ](../explanation/differences-from-official.md).

Prod5 files have no such HDU: `provided_sensitivity` returns `None`.

## Next

- Other quantities (effective area, angular and energy resolution, background):
  [Python API](../reference/python-api.md).
- Read the same file without gammapy: [Read the FITS directly](../how-to/read-fits-directly.md).
