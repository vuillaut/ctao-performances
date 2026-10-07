import numpy as np

from ctao_perf.ascii import ascii_table, plot_snippet
from ctao_perf.curves import Curve
from ctao_perf.figures import FigureResult


def _result():
    edges = np.array([1.0, 2.0, 4.0, 8.0])
    curves = [
        Curve.binned(edges, [1e-12, np.nan, 3e-12], "North (50 h)"),
        Curve(np.array([1.0, 3.0, 5.0]), np.array([2.0, 4.0, 6.0]), label="a line"),
    ]
    return FigureResult("demo", "Demo figure", "caption", None, curves,
                        "Energy [TeV]", "Flux [erg cm-2 s-1]", hline=1.0)


def test_table_drops_nan_and_names_series():
    text = ascii_table(_result(), ["Release: test"])
    lines = text.splitlines()
    assert lines[0] == "# Demo figure" and "# Release: test" in lines
    assert "#   North_50_h = North (50 h)" in lines
    rows = [l for l in lines if not l.startswith("#")]
    assert len(rows) == 2 + 3  # one NaN row dropped
    assert rows[0].split()[0] == "North_50_h"
    assert rows[-1].split()[2] == "nan"  # a line has no bin edges


def test_snippet_reads_the_file_it_describes(tmp_path, monkeypatch):
    """The ASCII file and the snippet must work together, whatever the comment lines."""
    import matplotlib

    matplotlib.use("Agg")
    result = _result()
    (tmp_path / "demo.dat").write_text(ascii_table(result, ["Release: test", "a = b"]))
    code = plot_snippet(result, "demo.dat").replace("plt.show()", "")
    monkeypatch.chdir(tmp_path)
    namespace = {}
    exec(compile(code, "snippet", "exec"), namespace)
    ax = namespace["ax"]
    assert len(ax.get_legend().get_texts()) == 2
    assert ax.get_xscale() == "log" and ax.get_ylabel() == "Flux [erg cm-2 s-1]"
    assert len(ax.lines) >= 2 and "axhline" in code  # data line(s) and the reference line


def test_series_tokens_stay_unique_and_text(tmp_path, monkeypatch):
    """Labels that collapse to the same token, or to a number, must still plot correctly."""
    import matplotlib

    matplotlib.use("Agg")
    edges = np.array([1.0, 2.0, 4.0])
    curves = [Curve.binned(edges, [1.0, 2.0], "50 h"), Curve.binned(edges, [3.0, 4.0], "50 h"),
              Curve.binned(edges, [5.0, 6.0], "50")]
    result = FigureResult("dup", "Duplicates", "", None, curves, "E [TeV]", "y", yscale="linear")
    text = ascii_table(result)
    assert "#   50_h = 50 h" in text and "#   50_h_2 = 50 h" in text and "#   50 = 50" in text
    (tmp_path / "dup.dat").write_text(text)
    code = plot_snippet(result, "dup.dat").replace("plt.show()", "")
    monkeypatch.chdir(tmp_path)
    ns = {}
    exec(compile(code, "snippet", "exec"), ns)
    ys = sorted(float(l.get_ydata()[0]) for l in ns["ax"].lines if len(l.get_ydata()) == 2)
    assert ys == [1.0, 3.0, 5.0]  # each series got only its own rows
