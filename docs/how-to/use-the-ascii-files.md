# Use the ASCII files of the figures

Every figure on the website, and every figure made by `ctao-perf figures`, comes with:

- `<id>.dat`: the plotted points, as text;
- `<id>.py`: a Python script that reads the `.dat` file and plots it again.

On the website, the links are under each figure; the script is also shown in a collapsible block.
Download the two files into the same folder and run `python <id>.py`.

## Format of the `.dat` file

Lines starting with `#` are comments: the title, the release and its DOI, the data source, the
meaning of x and y, and the legend label of each series. Then one row per point:

```
# series x xlo xhi y
CTAO_Southern_Array 1.584893e-02 1.258925e-02 1.995262e-02 7.137663e-11
```

| Column | Meaning |
|---|---|
| `series` | name of the curve, without spaces; the comments give its legend label |
| `x` | x value of the point: the geometric centre of the bin for binned data |
| `xlo`, `xhi` | edges of the bin, or `nan` for a curve drawn as a line |
| `y` | y value, in the unit given in the header |

Units are in the `# x:` and `# y:` lines; energies are in TeV. Points with no value (NaN) are
left out. Floats are written with 7 significant digits.

## Read it without the script

```python
import numpy as np
columns = [("series", "U40"), ("x", float), ("xlo", float), ("xhi", float), ("y", float)]
d = np.genfromtxt("sensitivity-north-south.dat", dtype=columns, encoding="utf-8")
south = d[d["series"] == "CTAO_Southern_Array"]
```

Give the column names and types explicitly: numpy cannot take them from the commented header line
when other comment lines come before the data, and it would read a series named `50` as a number.
The `U40` must be at least the length of the longest series token (the scripts set it for you).
Two curves whose labels give the same token get `_2`, `_3`... added, so the tokens stay unique.
With pandas:

```python
import pandas as pd
df = pd.read_csv("sensitivity-north-south.dat", sep=r"\s+", comment="#",
                 names=["series", "x", "xlo", "xhi", "y"])
```

## What the script does

Binned curves are drawn with `errorbar` (a point per bin, with a bar over the bin); the others
with `plot`. Axis labels and scales are the ones of the figure. The script uses plain matplotlib
and not the style of this repository, so the figure looks different from the PNG.

The `.dat` file of a figure is exactly what was plotted: it is written from the same arrays.
For the figures with a reference line (the ratio figures), the script draws it too.

## Credit

The files are derived from the CTAO instrument response functions (CC BY 4.0). Cite the DOI of the
release given in the header. Files made from the gammapy source are not official CTAO numbers.
