# Add a figure

A figure is a generator in `src/ctao_perf/figures.py` registered with `@producer`. It runs once per
release and per source (`gammapy` and `root`), and every figure gets a PNG, an ASCII data file and a
plot script for free.

```python
@producer
def effective_area_ratio(ctx: Context):
    rel = ctx.release
    fig, ax = new_figure()
    curves = []
    for i, site in enumerate(ctx.sites):
        if not ctx.src.exists(site.key):
            continue
        curve = ctx.src.effective_area(site.key).with_label(site.label)   # a Curve
        draw_curve(ax, curve, i)
        curves.append(curve)
    ax.set(xscale="log", yscale="log", xlabel=E_TRUE_LABEL, ylabel="Effective area [m$^2$]")
    ax.legend()
    yield FigureResult(
        id="effective-area-both",              # becomes <source>/<id>.png, .dat, .py
        title="Effective area of both sites",
        caption=ctx.caption(gammapy="From the FITS files.", root="From the ROOT files."),
        figure=ctx.finish(fig, ax),             # applies the style and the DOI credit
        curves=curves,                          # what goes in the .dat file
        xlabel="True gamma-ray energy E_T [TeV]", ylabel="Effective area [m2]",
        xscale="log", yscale="log",             # for the plot script
    )
```

Rules that keep it working for every release and source:

- **Read data through `ctx.src`.** It is the active source: `GammapySource` or `RootSource`, with the
  same methods (`sensitivity`, `angular_resolution`, `energy_resolution`, `effective_area`,
  `background_rate`, `sensitivity_offaxis`), each returning a `Curve` in the units of the figure axes.
  `ctx.src.exists(...)` tells whether a combination of files is present. To use only one source, write
  `@producer(sources=("gammapy",))`; then `ctx.gammapy` and `ctx.root` are both available.
- **Add what a source lacks to the source**, not to the producer, so that other figures can use it:
  a method in `sources.py`, and for ROOT a reader in `root.py`.
- **Pass the curves you draw to `FigureResult(curves=...)`.** The `.dat` file is written from them,
  so it is exactly what the figure shows. Use `draw_curve` to draw them. Give the `xlabel` and `ylabel`
  in plain text (units included): they go in the header of the `.dat` file and in the script.
- **Skip what is missing, do not fail.** Use `if not ctx.src.exists(...): continue`, or return early when
  a release lacks an option (see `sensitivity_vs_time`, which returns when `short_term` is empty).
  `make_figures` also catches `FileNotFoundError` and logs a warning.
- **Take site-dependent values from `Site`** (`site.e_min`, `site.label`), not from constants.
  `ctx.mask(site, curve)` hides the bins below the lowest energy of the official figures.
- `id` must be unique within a source. If one producer yields one figure per site, suffix the id with
  `-{site.key}`.

To show an official figure next to yours on the website, add its file name to `reference_figures` in
each release YAML under the same `id`. The test `test_reference_figures_have_producers` checks the id
prefix against a list in `tests/test_config.py`: add your prefix there.

Run only your producer, for one source:

```bash
ctao-perf figures prod6-v1.0 --only effective_area_ratio --sources root
```

`--only` takes function names, as printed by `ctao-perf list`.
