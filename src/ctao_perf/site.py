"""Static website presenting the figures of every release."""

from __future__ import annotations

import html
import json
import logging
import os
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
@media (min-width: 900px) { .pair.two { grid-template-columns: 1fr 1fr; } }
.pair figure { margin: 0; }
.pair img { width: 100%; height: auto; background: var(--img-bg); border-radius: 6px;
  border: 1px solid var(--border); }
figcaption { font-size: .85rem; color: var(--muted); margin-top: 4px; }
.toc { columns: 2 260px; padding-left: 18px; font-size: .95rem; }
.note { border-left: 3px solid var(--accent); padding: 4px 12px; margin: 16px 0; font-size: .95rem; }
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


def build_release_page(release: Release, manifest, data_dir, release_out: Path):
    ref_dir = release_out / "official"
    ref_dir.mkdir(parents=True, exist_ok=True)
    sections, toc = [], []
    for item in manifest:
        ref = _find_reference(release, data_dir, item["reference"])
        ours = (f'<figure><img src="figures/{item["file"]}" alt="{html.escape(item["title"])}" '
                f'loading="lazy"><figcaption>Reproduced from the FITS IRFs</figcaption></figure>')
        theirs = ""
        if ref is not None:
            shutil.copy2(ref, ref_dir / ref.name)
            theirs = (f'<figure><img src="official/{ref.name}" alt="Official figure" loading="lazy">'
                      f'<figcaption>Official figure shipped with the release</figcaption></figure>')
        toc.append(f'<li><a href="#{item["id"]}">{html.escape(item["title"])}</a></li>')
        sections.append(f"""
<section class="figure card" id="{item['id']}">
  <h2>{html.escape(item['title'])}</h2>
  <p class="muted">{html.escape(item['caption'])}</p>
  <div class="pair{' two' if theirs else ''}">{ours}{theirs}</div>
</section>""")

    body = f"""
<nav class="crumbs"><a href="../index.html">All releases</a></nav>
<header>
  <h1>{html.escape(release.title)}</h1>
  <p class="muted">{html.escape(release.description)}</p>
  <p>Data: <a href="https://doi.org/{release.doi}">doi:{release.doi}</a> ·
     zenith {release.zenith}°, {release.azimuth}, {release.condition} sky ·
     source offset {release.offset}</p>
</header>
<div class="note">Sensitivities are computed with gammapy from the effective area, PSF, energy
dispersion and background of the FITS files (on region = 68% PSF containment, off/on ratio
{1 / release.sensitivity.alpha:g}, {release.sensitivity.n_sigma:g}σ, ≥{release.sensitivity.gamma_min:g}
excess events, S/B ≥ {release.sensitivity.bkg_syst_fraction:g}). The official curves come from
an analysis of the full simulations with cuts optimised per energy bin, so differences of tens
of percent are expected, mostly near the energy threshold and at the highest energies.</div>
<ul class="toc">{''.join(toc)}</ul>
{''.join(sections)}
"""
    (release_out / "index.html").write_text(_page(release.title, body, depth=1))
    (release_out / "manifest.json").write_text(json.dumps(manifest, indent=2))


def build_index(entries, out_dir: Path):
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
    body = f"""
<header>
  <h1>CTAO performance</h1>
  <p class="muted">Performance figures of the Cherenkov Telescope Array Observatory,
  reproduced with <a href="https://gammapy.org">gammapy</a> from the instrument response
  functions published on Zenodo, and compared with the official figures.</p>
</header>
<div class="releases">{''.join(cards)}</div>
"""
    (out_dir / "index.html").write_text(_page("CTAO performance", body))
    (out_dir / "style.css").write_text(CSS)
    (out_dir / ".nojekyll").write_text("")
