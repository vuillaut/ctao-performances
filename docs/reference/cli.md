# Command line

```
ctao-perf [-v] [--data-dir DIR] {list,download,figures,site} ...
```

Global options go **before** the sub-command.

| Option | Default | Meaning |
|---|---|---|
| `-v`, `--verbose` | off | log at INFO for third-party loggers too (ctao_perf always logs INFO) |
| `--data-dir DIR` | `./data` | where IRFs are downloaded and read |

`releases` arguments are bundled release names (`prod6-v1.0`) or paths to a
YAML file. Omitted, they mean every bundled release.

## `ctao-perf list`

Prints bundled releases (name, title, Zenodo record) and the names of the
figure producers.

## `ctao-perf download [releases...] [--force] [--root]`

Downloads each release zip from Zenodo, verifies the MD5 reported by the
Zenodo API, unpacks it and flattens every FITS file into
`<data-dir>/<name>/irfs/`. Skipped when `<data-dir>/<name>/.unpacked` exists.
`--force` downloads and unpacks again. `--root` also fetches the ROOT bundle (about 1.1 GB for Prod6, 0.9 GB for Prod5),
keeps the files the figures need (32 for Prod6, 18 for Prod5) in `<data-dir>/<name>/root/` and deletes the zip; it is skipped
for releases without a `zenodo.root_file`. See [ROOT files](../data/root-files.md).

## `ctao-perf figures [releases...] [-o DIR] [--only PRODUCER ...] [--sources {gammapy,root} ...]`

Writes, for each figure, a PNG, an ASCII data file and a plot script to
`DIR/<release>/<source>/` (default `figures`), where `<source>` is `gammapy` (recomputed from the
FITS IRFs) or `root` (official curves from the ROOT files). Both by default; a source whose files are
not downloaded is skipped with a warning. It does not download: run `download` first.
`--only` restricts to the named producers.

## `ctao-perf site [releases...] [-o DIR] [--only PRODUCER ...] [--sources ...] [--docs-dir DIR]`

Downloads if needed (FITS, and ROOT when `root` is among the sources), makes the figures, renders the
Markdown documentation from `--docs-dir` (default `./docs`) and writes the static website to `DIR`
(default `public`):

```
public/
  index.html  style.css  .nojekyll
  <release>/
    index.html  manifest.json
    figures/gammapy/   <id>.png  <id>.dat  <id>.py   recomputed with gammapy
    figures/root/      <id>.png  <id>.dat  <id>.py   official curves from ROOT
    official/*.png     copied from the Zenodo archive
  docs/                the documentation, as HTML
```

`manifest.json` lists one entry per (source, figure): `id`, `title`, `caption`, `source`, `file`,
`data`, `script` and `reference`.

## Exit status

0 on success. A missing release raises `FileNotFoundError` listing the bundled
names. A producer that cannot find its input files is skipped with a warning,
not an error.
