"""Command line interface: ``ctao-perf {list,download,figures,site}``."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import available_releases, load_release
from .download import fetch
from .figures import PRODUCERS, make_figures
from .site import build_index, build_release_page


def _releases(names):
    return [load_release(n) for n in names] if names else available_releases()


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

    for name, help_ in [("figures", "make the figures"),
                        ("site", "download, make figures and build the website")]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("releases", nargs="*", help="release names or YAML files (default: all)")
        p.add_argument("-o", "--output", type=Path,
                       default=Path("public" if name == "site" else "figures"))
        p.add_argument("--only", nargs="+", metavar="PRODUCER",
                       help="restrict to some figure producers (see `ctao-perf list`)")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("ctao_perf").setLevel(logging.INFO)

    if args.command == "list":
        for r in available_releases():
            print(f"{r.name:14s} {r.title}  (zenodo {r.zenodo_record})")
        print("\nfigure producers:", ", ".join(p.__name__ for p in PRODUCERS))
        return

    releases = _releases(args.releases)

    if args.command == "download":
        for r in releases:
            fetch(r, args.data_dir, force=args.force)
        return

    if args.command == "figures":
        for r in releases:
            make_figures(r, args.data_dir, args.output / r.name, only=args.only)
        return

    if args.command == "site":
        args.output.mkdir(parents=True, exist_ok=True)
        entries = []
        for r in releases:
            fetch(r, args.data_dir)
            out = args.output / r.name
            manifest = make_figures(r, args.data_dir, out / "figures", only=args.only)
            build_release_page(r, manifest, args.data_dir, out)
            entries.append((r, manifest))
        build_index(entries, args.output)
        print(f"Website written to {args.output}/index.html")


if __name__ == "__main__":
    main()
