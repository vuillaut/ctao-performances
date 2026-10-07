# Pick the right IRF file

Which of the 192 (Prod6) or 162 (Prod5) files should you use? Work through the
axes in this order.

| Question | Choose |
|---|---|
| Which site? | `North` (La Palma) or `South` (Paranal) |
| Which sub-array? (Prod5 only) | the full array (`4LSTs09MSTs`, `14MSTs37SSTs`) unless you study a sub-array: `09MSTs` or `4LSTs` (North), `14MSTs` or `37SSTs` (South) |
| Which source zenith angle? | the closest one: 20°, 40°, 52° (Prod6 only), 60° |
| Which azimuth? | `AverageAz` for general work. `NorthAz` / `SouthAz` only if your pointing is toward magnetic North or South: the geomagnetic field matters, mostly for the North site |
| Which sky? (Prod6 only) | `dark` or `halfmoon` (sky brightness 5× dark) |
| Which observation time? | the one closest to yours: the cuts are optimised for it. 100 s (Prod6 only), 1800 s, 18000 s, 180000 s |

In code:

```python
library.path("North", 18000, zenith=40, azimuth="NorthAz", condition="halfmoon")
```

Use `library.exists(...)` to test a combination first. The release YAML lists
the available `zeniths` and `durations`; it does not list azimuths or
conditions, so a non-existent combination raises `FileNotFoundError` with a hint
to run `ctao-perf download`.

To list what is on disk:

```bash
ls data/prod6-v1.0/irfs | grep South-40deg-AverageAz
```

See [File naming](../data/file-naming.md) for the pattern.
