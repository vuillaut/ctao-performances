# Reproduce the figures from the ROOT files

The official figures of CTAO come from the ROOT files. `ctao-perf` draws the same quantities from
them with its own plotting code, next to the gammapy figures. This is the quickest way to get the
official numbers as a table.

## Command line

```bash
ctao-perf download --root prod6-v1.0        # ~1 GB download, keeps ~205 MB
ctao-perf figures prod6-v1.0 --sources root -o figures
```

Output, in `figures/prod6-v1.0/root/`:

```
sensitivity-durations-North.png / .dat / .py
sensitivity-north-south.png / .dat / .py
angular-resolution.png ...
```

Each figure comes with its data points and a plot script ([Use the ASCII files](use-the-ascii-files.md)).
Leave out `--sources` to also make the gammapy figures; `ctao-perf site` does both and puts the
official PNG next to them.

The figures made from ROOT, with the histograms they read:

| Figure id | Histogram |
|---|---|
| `sensitivity-durations-<site>`, `sensitivity-north-south`, `sensitivity-zenith-<site>` | `DiffSens` |
| `offaxis-sensitivity-<site>` | `DiffSens_offaxis` |
| `angular-resolution` | `AngResEtrue` |
| `energy-resolution` | `ERes` |
| `effective-area-<site>` | `EffectiveAreaNoTheta2cut` |
| `effective-area-direction-cuts-<site>` | `EffectiveArea` (ROOT only) |
| `background-rate` | `BGRatePerSqDeg` |

There is no ROOT counterpart for `sensitivity-time-<site>`, `sensitivity-validation[-onaxis]-<site>`
and `sensitivity-ratio[-onaxis]-<site>`, which need the gammapy calculation. The validation figures
read `DiffSens_offaxis` (offset bin of the source) and `DiffSens` (on axis) from the ROOT files.

## From Python

```python
from ctao_perf import load_release
from ctao_perf.sources import RootSource

release = load_release("prod6-v1.0")
official = RootSource(release, "data")

sens = official.sensitivity("South")          # 50 h, 20 deg, AverageAz, dark
print(sens.x, sens.y)                          # bin centres [TeV], E2 dN/dE [erg cm-2 s-1]
sens_5h = official.sensitivity("South", 18000)
aeff = official.effective_area("South", direction_cut=True)
```

All methods return a `Curve` with energies in TeV. `RootSource` has the same methods as
`GammapySource`, so the two can be swapped in your code. For other histograms, use `uproot`
directly ([ROOT files](../data/root-files.md#reading-them)).

## Another zenith angle, azimuth or sky condition

Only the default azimuth and sky condition are extracted. To use another one, extract it
yourself from the Zenodo bundle, into `data/<release>/root/`, with the same file name, or change
`azimuth` and `condition` in a copy of the release YAML.
