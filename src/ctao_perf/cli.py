"""Command line interface: ``ctao-perf {list,download,figures,site}``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import available_releases, load_release
from .download import fetch, fetch_root
from .figures import ALL_SOURCES, PRODUCERS, make_figures
from .site import build_docs, build_index, build_release_page


def _releases(names):
    return [load_release(n) for n in names] if names else available_releases()


def _has_root(release):
    """True when the release has a ROOT bundle; otherwise say so (only FITS figures then)."""
    if not release.zenodo_root_file:
        logging.getLogger("ctao_perf").info("%s: no ROOT bundle configured, FITS figures only",
                                            release.name)
    return bool(release.zenodo_root_file)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ctao-perf", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=Path("data"),
                        help="where IRFs are downloaded (default: ./data)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list bundled releases and figure producers")

    p = sub.add_parser("download", help="download and unpack IRFs from Zenodo")
    p.add_argument("releases", nargs="*", help="release names or YAML files (default: all)")
    p.add_argument("--force", action="store_true")
    p.add_argument("--root", action="store_true",
                   help="also download the ROOT files with the official curves (~1 GB per release)")

    for name, help_ in [("figures", "make the figures"),
                        ("site", "download, make figures and build the website")]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("releases", nargs="*", help="release names or YAML files (default: all)")
        p.add_argument("-o", "--output", type=Path,
                       default=Path("public" if name == "site" else "figures"))
        p.add_argument("--only", nargs="+", metavar="PRODUCER",
                       help="restrict to some figure producers (see `ctao-perf list`)")
        p.add_argument("--sources", nargs="+", choices=list(ALL_SOURCES), default=list(ALL_SOURCES),
                       help="data to draw the figures from (default: both)")
        if name == "site":
            p.add_argument("--docs-dir", type=Path, default=Path("docs"),
                           help="Markdown documentation to render (default: ./docs)")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("ctao_perf").setLevel(logging.INFO)

    if args.command == "list":
        for r in available_releases():
            print(f"{r.name:14s} {r.title}  (zenodo {r.zenodo_record})")
        print("\nfigure producers (sources):",
              ", ".join(f"{p.__name__} ({'+'.join(p.sources)})" for p in PRODUCERS))
        return

    releases = _releases(args.releases)

    if args.command == "download":
        for r in releases:
            fetch(r, args.data_dir, force=args.force)
            if args.root and _has_root(r):
                fetch_root(r, args.data_dir, force=args.force)
        return

    if args.command == "figures":
        for r in releases:
            make_figures(r, args.data_dir, args.output / r.name, only=args.only,
                         sources=args.sources)
        return

    if args.command == "site":
        args.output.mkdir(parents=True, exist_ok=True)
        entries = []
        for r in releases:
            fetch(r, args.data_dir)
            if "root" in args.sources and _has_root(r):
                fetch_root(r, args.data_dir)
            out = args.output / r.name
            manifest = make_figures(r, args.data_dir, out / "figures", only=args.only,
                                    sources=args.sources)
            build_release_page(r, manifest, args.data_dir, out, docs=args.docs_dir.is_dir())
            entries.append((r, manifest))
        has_docs = build_docs(args.docs_dir, args.output)
        build_index(entries, args.output, docs=has_docs)
        print(f"Website written to {args.output}/index.html")


if __name__ == "__main__":
    main()
