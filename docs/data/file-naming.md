# File naming

## Prod6

```
Prod6-CTAO-South-40deg-NorthAz-2LSTs14MSTs37SSTs-halfmoon-180000s-v1.0.fits.gz
  │     │     │     │     │          │              │         │      └ release version
  │     │     │     │     │          │              │         └ optimisation time, seconds
  │     │     │     │     │          │              └ sky: dark | halfmoon
  │     │     │     │     │          └ telescopes: 2 LSTs, 14 MSTs, 37 SSTs
  │     │     │     │     └ azimuth: AverageAz | NorthAz | SouthAz
  │     │     │     └ zenith angle: 20 | 40 | 52 | 60
  │     │     └ site: North | South
  │     └ CTAO
  └ production
```

Pattern in the YAML:
`Prod6-CTAO-{site}-{zenith}deg-{azimuth}-{telescopes}-{condition}-{duration}s-v1.0.fits.gz`

Telescopes by site: North `4LSTs09MSTs`; South `2LSTs14MSTs37SSTs`.

## Prod5

```
Prod5-South-20deg-AverageAz-14MSTs37SSTs.180000s-v0.1.fits.gz
```

Pattern: `Prod5-{site}-{zenith}deg-{azimuth}-{telescopes}.{duration}s-v0.1.fits.gz`.
Note the `.` before the duration. No sky condition: all Prod5 files are for dark sky.

Telescope strings found on disk:

| Site | Full array | Sub-arrays |
|---|---|---|
| North | `4LSTs09MSTs` | `4LSTs`, `09MSTs` |
| South | `14MSTs37SSTs` | `14MSTs`, `37SSTs` |

`ctao-perf` only uses the full arrays through `Release.irf_filename`. For a
sub-array file, build the name yourself.

## Meaning of the labels

| Label | Meaning |
|---|---|
| zenith | zenith angle of the pointing |
| `AverageAz` | average over the two magnetic directions: use it by default |
| `NorthAz`, `SouthAz` | pointing toward magnetic North or South, where the geomagnetic field affects showers differently (large effect at the North site) |
| `dark`, `halfmoon` | sky brightness; `halfmoon` is 5 × the dark level |
| duration | observation time for which the analysis cuts were optimised: 100 s, 30 min (1800 s), 5 h (18000 s), 50 h (180000 s). Not the livetime you must use |

## ROOT files

Same names with `.root` instead of `.fits.gz`; see [ROOT files](root-files.md).

Use `Release.irf_filename(...)` or `IRFLibrary.path(...)` instead of building
names by hand. See [Pick the right IRF file](../how-to/select-an-irf-file.md).
