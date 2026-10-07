# Run the tests and the CI pipeline locally

## Tests

```bash
pip install -e ".[test]"
pytest                          # config and unit tests only (data tests skip)
ctao-perf download --root       # then the data tests run too, ROOT ones included
pytest -v
```

Tests marked `data` need `./data/<release>/irfs`. They skip when the files are
absent. They check that:

- file names follow the pattern of each release (`test_config.py`);
- `fill_edisp` fills empty high-energy columns (`test_performance.py`);
- Prod5 South 50 h has its minimum sensitivity between 0.8 and 1.2 × 10⁻¹³ erg cm⁻² s⁻¹;
- Prod6 sensitivity agrees with the tabulated one within a factor 0.7–1.4 from 0.1 to 50 TeV;
- Prod6 South angular resolution at 1 TeV is between 0.045° and 0.06°;
- the gammapy sensitivity is 0.9–1.4 times the ROOT one from 0.1 to 50 TeV, for Prod5 and Prod6 (`test_root.py`);
- the ROOT readers handle empty bins, direction-cut variants and missing files (synthetic ROOT files
  written with uproot), and every ASCII file works with the script that goes with it (`test_ascii.py`).

## What CI does

`.github/workflows/pages.yml`, on each push to `main`, pull request or manual run:

1. install with `uv`, Python 3.12;
2. restore `data/` from cache, keyed on `hashFiles('releases/*.yaml')`;
3. `ctao-perf download --root` (FITS and, for Prod6, ROOT);
4. `pytest -v`;
5. `ctao-perf site -o public` (figures from both sources, ASCII files, documentation);
6. upload `public/` as a Pages artifact.

Deployment to GitHub Pages runs only on `main`. Pull requests build but do not
deploy.

## Reproduce the CI build

```bash
ctao-perf site -o public && python -m http.server -d public
```
