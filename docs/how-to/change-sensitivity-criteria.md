# Change the sensitivity criteria

The criteria are per release, in the `sensitivity:` block of the YAML. Every
key is optional; these are the defaults:

```yaml
sensitivity:
  n_sigma: 5.0              # detection significance (Li & Ma)
  gamma_min: 10.0           # minimum number of excess events
  bkg_syst_fraction: 0.05   # excess must be >= 5 % of the background
  alpha: 0.2                # on/off exposure ratio (1 / 5 off regions)
  containment: 0.68         # PSF containment fraction used for the on region
```

To change them for one run from Python, build a `SensitivityCriteria`:

```python
from ctao_perf.config import SensitivityCriteria
from ctao_perf import performance as perf

strict = SensitivityCriteria(n_sigma=3, gamma_min=5)
axis, e2dnde, _ = perf.sensitivity(irfs, 50 * u.h, "ctao_south", criteria=strict)
```

To change the energy binning or the source offset:

```python
axis = perf.log_energy_axis(lo_exp=-1.5, hi_exp=2.0, per_decade=10)
perf.sensitivity(irfs, 50 * u.h, "ctao_south", energy_axis=axis, offset=1.5 * u.deg)
```

Offsets must lie inside the IRF offset range: 0–6° for the effective area, PSF
and energy dispersion (1°-wide bins), ±6° in detector coordinates for the
background (0.2° bins). See [FITS contents](../data/fits-contents.md#the-offset-axes).

Do not expect to reproduce the official curves more closely by tuning these
numbers: the official analysis also optimises cuts per energy bin.
See [Differences from the official figures](../explanation/differences-from-official.md).
