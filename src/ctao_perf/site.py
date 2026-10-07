"""Static website presenting the figures of every release."""

from __future__ import annotations

import html
import json
import logging
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .config import Release
from .download import archive_dir

log = logging.getLogger(__name__)

REPO_URL = "https://github.com/" + os.environ.get("GITHUB_REPOSITORY", "vuillaut/ctao-performances")

CSS = """
:root {
  --bg: #fbfbfa; --fg: #1d1d1f; --muted: #5f6368; --card: #ffffff;
  --border: #e3e3e0; --accent: #c0254b; --img-bg: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #151517; --fg: #ececec; --muted: #a0a0a6; --card: #1f1f22;
    --border: #333338; --accent: #ff6f8e; --img-bg: #f4f4f2;
  }
}
:root[data-theme="dark"] {
  --bg: #151517; --fg: #ececec; --muted: #a0a0a6; --card: #1f1f22;
  --border: #333338; --accent: #ff6f8e; --img-bg: #f4f4f2;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 1240px; margin: 0 auto; padding: 32px 16px 64px; }
header { margin-bottom: 28px; }
h1 { font-size: 1.9rem; margin: 0 0 6px; letter-spacing: -0.01em; }
h2 { font-size: 1.2rem; margin: 0 0 6px; }
a { color: var(--accent); }
.muted { color: var(--muted); }
nav.crumbs { font-size: .9rem; margin-bottom: 12px; }
.releases { display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 18px; }
.card img { width: 100%; background: var(--img-bg); border-radius: 6px; }
.figure { margin: 0 0 28px; }
.pair { display: grid; gap: 14px; grid-template-columns: 1fr; margin-top: 10px; }
@media (min-width: 900px) { .pair.n2 { grid-template-columns: 1fr 1fr; } }
@media (min-width: 1200px) { .pair.n3 { grid-template-columns: 1fr 1fr 1fr; } }
.dl { font-size: .85rem; margin: 4px 0; }
details pre { max-height: 22em; overflow: auto; }
.pair figure { margin: 0; }
.pair img { width: 100%; height: auto; background: var(--img-bg); border-radius: 6px;
  border: 1px solid var(--border); }
figcaption { font-size: .85rem; color: var(--muted); margin-top: 4px; }
.toc { columns: 2 260px; padding-left: 18px; font-size: .95rem; }
.note { border-left: 3px solid var(--accent); padding: 4px 12px; margin: 16px 0; font-size: .95rem; }
nav.top { font-size: .9rem; margin-bottom: 12px; display: flex; gap: 16px; flex-wrap: wrap; }
.doc { max-width: 900px; }
.doc table { border-collapse: collapse; display: block; overflow-x: auto; font-size: .9rem; }
.doc th, .doc td { border: 1px solid var(--border); padding: 4px 8px; text-align: left; vertical-align: top; }
.doc pre { background: var(--card); border: 1px solid var(--border); border-radius: 6px;
  padding: 10px 12px; overflow-x: auto; font-size: .85rem; }
.doc code { font-size: .88em; }
.doc :not(pre) > code { background: var(--card); border: 1px solid var(--border);
  border-radius: 4px; padding: 0 4px; }
.doc h1 { font-size: 1.7rem; } .doc h2 { font-size: 1.3rem; margin-top: 1.8em; }
.doc h3 { font-size: 1.1rem; margin-top: 1.4em; }
footer { margin-top: 48px; font-size: .85rem; color: var(--muted); }
"""


def _page(title, body, depth=0):
    root = "../" * depth
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<main>
{body}
<footer>
Generated {stamp} by <a href="{REPO_URL}">ctao-performances</a> v{__version__}
from the public CTAO instrument response functions, using
<a href="https://gammapy.org">gammapy</a>. These are not official CTAO products;
refer to the <a href="https://www.ctao.org/for-scientists/performance/">CTAO performance page</a>.<br>
IRFs and official figures &copy; CTAO, licensed under
<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>;
see the DOI of each release. Reproduced figures: CC BY 4.0. Code: BSD 3-Clause.
</footer>
</main>
</body>
</html>
"""


def _find_reference(release: Release, data_dir, name):
    if not name:
        return None
    matches = sorted(archive_dir(release, data_dir).rglob(name))
    return matches[0] if matches else None


SOURCE_CAPTIONS = {
    "gammapy": "Recomputed with gammapy from the FITS IRFs",
    "root": "Official curves read from the ROOT files",
}


def _group_by_id(manifest):
    """``[(id, [entries...])]`` in order of first appearance, entries ordered by source."""
    groups = {}
    for item in manifest:
        groups.setdefault(item["id"], []).append(item)
    order = {"gammapy": 0, "root": 1}
    return [(k, sorted(v, key=lambda m: order.get(m["source"], 9))) for k, v in groups.items()]


def _variant_html(variant, release_out: Path):
    snippet = (release_out / "figures" / variant["script"]).read_text(encoding="utf-8")
    return f"""<figure><img src="figures/{variant['file']}" alt="{html.escape(variant['title'])}" loading="lazy">
<figcaption><strong>{SOURCE_CAPTIONS[variant['source']]}.</strong> {html.escape(variant['caption'])}</figcaption>
<p class="dl"><a href="figures/{variant['data']}" download>data points (.dat)</a> ·
<a href="figures/{variant['script']}" download>plot script (.py)</a></p>
<details><summary>Plot it from the data file</summary><pre><code>{html.escape(snippet)}</code></pre></details>
</figure>"""


def build_release_page(release: Release, manifest, data_dir, release_out: Path, docs=True):
    """Write the page of one release; ``docs=False`` omits the links to the documentation."""
    ref_dir = release_out / "official"
    ref_dir.mkdir(parents=True, exist_ok=True)
    sections, toc = [], []
    for fig_id, variants in _group_by_id(manifest):
        first = variants[0]
        panels = [_variant_html(v, release_out) for v in variants]
        ref = _find_reference(release, data_dir, first["reference"])
        if ref is not None:
            shutil.copy2(ref, ref_dir / ref.name)
            panels.append(f'<figure><img src="official/{ref.name}" alt="Official figure" loading="lazy">'
                          f'<figcaption><strong>Official figure shipped with the release.</strong> '
                          f'Made by CTAO with its own plotting code; it may also show other '
                          f'instruments.</figcaption></figure>')
        toc.append(f'<li><a href="#{fig_id}">{html.escape(first["title"])}</a></li>')
        sections.append(f"""
<section class="figure card" id="{fig_id}">
  <h2>{html.escape(first['title'])}</h2>
  <div class="pair n{len(panels)}">{''.join(panels)}</div>
</section>""")

    docs_link = ' <a href="../docs/index.html">Documentation</a>' if docs else ""
    docs_details = ('<a href="../docs/explanation/differences-from-official.html">Details</a> · '
                    '<a href="../docs/data/index.html">about the data</a>. ' if docs else "")
    body = f"""
<nav class="top"><a href="../index.html">All releases</a>{docs_link}</nav>
<header>
  <h1>{html.escape(release.title)}</h1>
  <p class="muted">{html.escape(release.description)}</p>
  <p>Data: <a href="https://doi.org/{release.doi}">doi:{release.doi}</a> ·
     zenith {release.zenith}°, {release.azimuth}, {release.condition} sky ·
     source offset {release.offset}</p>
</header>
<div class="note">Each figure is shown up to three times: <strong>recomputed with gammapy</strong> from
the FITS IRFs (on region = 68% PSF containment, off/on ratio
{1 / release.sensitivity.alpha:g}, {release.sensitivity.n_sigma:g}σ, ≥{release.sensitivity.gamma_min:g}
excess events, S/B ≥ {release.sensitivity.bkg_syst_fraction:g}); the <strong>official curves read
from the ROOT files</strong> (same histograms as CTAO's figures, replotted here); and the
<strong>official PNG</strong> from the Zenodo archive. The gammapy curves use a simpler analysis
than CTAO's (cuts optimised per energy bin, full PSF), so expect differences of tens of percent,
mostly near the energy threshold and at the highest energies.
{docs_details}Each curve can be downloaded as an ASCII file.</div>
<ul class="toc">{''.join(toc)}</ul>
{''.join(sections)}
"""
    (release_out / "index.html").write_text(_page(release.title, body, depth=1), encoding="utf-8")
    (release_out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_index(entries, out_dir: Path, docs=True):
    cards = []
    for release, manifest in entries:
        thumb = next((m["file"] for m in manifest if m["id"] == "sensitivity-north-south"),
                     manifest[0]["file"] if manifest else None)
        img = f'<img src="{release.name}/figures/{thumb}" alt="" loading="lazy">' if thumb else ""
        cards.append(f"""
<a class="card" href="{release.name}/index.html" style="text-decoration:none;color:inherit">
  {img}
  <h2 style="margin-top:12px">{html.escape(release.title)}</h2>
  <p class="muted">{html.escape(release.description)}</p>
  <p class="muted">{len(manifest)} figures · doi:{release.doi}</p>
</a>""")
    docs_nav = '<nav class="top"><a href="docs/index.html">Documentation</a></nav>\n' if docs else ""
    body = f"""
{docs_nav}<header>
  <h1>CTAO performance</h1>
  <p class="muted">Performance figures of the Cherenkov Telescope Array Observatory,
  reproduced with <a href="https://gammapy.org">gammapy</a> from the instrument response
  functions published on Zenodo, and compared with the official figures.</p>
</header>
<div class="releases">{''.join(cards)}</div>
"""
    (out_dir / "index.html").write_text(_page("CTAO performance", body), encoding="utf-8")
    (out_dir / "style.css").write_text(CSS, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("")


def _md_links_to_html(text):
    """Point links to other Markdown pages of the docs at their HTML version."""
    return re.sub(r'href="([^"#:]+)\.md(#[^"]*)?"', r'href="\1.html\2"', text)


def build_docs(docs_dir: Path, out_dir: Path) -> bool:
    """Render the Markdown documentation in ``docs_dir`` to ``out_dir/docs``.

    Returns False, with a warning, when there is no such folder.
    """
    import markdown

    docs_dir = Path(docs_dir)
    if not docs_dir.is_dir():
        log.warning("No documentation folder at %s: the site is built without documentation", docs_dir)
        return False
    target = out_dir / "docs"
    for src in sorted(docs_dir.rglob("*.md")):
        rel = src.relative_to(docs_dir)
        text = src.read_text(encoding="utf-8")
        title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), rel.stem)
        content = markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "attr_list"])
        depth = len(rel.parts)  # docs/ is one level below the site root
        root = "../" * depth
        nav = (f'<nav class="top"><a href="{root}index.html">All releases</a> '
               f'<a href="{root}docs/index.html">Documentation</a> '
               + " ".join(f'<a href="{root}docs/{d}/index.html">{d}</a>'
                          for d in ("tutorials", "how-to", "reference", "explanation", "data"))
               + "</nav>")
        body = f'{nav}<article class="doc">{_md_links_to_html(content)}</article>'
        dest = (target / rel).with_suffix(".html")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_page(f"{title} - ctao-perf", body, depth=depth), encoding="utf-8")
    log.info("Documentation written to %s", target)
    return True
