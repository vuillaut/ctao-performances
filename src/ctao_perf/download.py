"""Download and unpack IRF releases from Zenodo."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from .config import Release

log = logging.getLogger(__name__)

ZENODO_API = "https://zenodo.org/api/records/{record}"
DONE_MARKER = ".unpacked"
ROOT_DONE_MARKER = ".root_unpacked"


def zenodo_file_info(record, filename):
    """Download URL and checksum ("md5:...") of a file in a Zenodo record."""
    with urllib.request.urlopen(ZENODO_API.format(record=record), timeout=60) as resp:
        meta = json.load(resp)
    for f in meta["files"]:
        if f["key"] == filename:
            return f["links"]["self"], f.get("checksum")
    available = ", ".join(f["key"] for f in meta["files"])
    raise FileNotFoundError(f"{filename} not in Zenodo record {record}. Files: {available}")


def _md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def _download(url, dest, checksum=None):
    tmp = dest.with_suffix(dest.suffix + ".part")
    log.info("Downloading %s", url)
    with urllib.request.urlopen(url, timeout=600) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out, length=1 << 20)
    if checksum and checksum.startswith("md5:") and _md5(tmp) != checksum[4:]:
        tmp.unlink()
        raise OSError(f"Checksum mismatch for {url}")
    tmp.rename(dest)


def release_dir(release: Release, data_dir) -> Path:
    return Path(data_dir) / release.name


def irf_dir(release: Release, data_dir) -> Path:
    return release_dir(release, data_dir) / "irfs"


def root_dir(release: Release, data_dir) -> Path:
    """ROOT files holding the official curves (see :func:`fetch_root`)."""
    return release_dir(release, data_dir) / "root"


def archive_dir(release: Release, data_dir) -> Path:
    """Unpacked Zenodo bundle (README, official figures, ...)."""
    return release_dir(release, data_dir) / "archive"


def fetch(release: Release, data_dir, force=False) -> Path:
    """Download the release bundle and unpack every IRF into ``<data_dir>/<name>/irfs``.

    Already unpacked releases are skipped unless ``force`` is set.
    """
    root = release_dir(release, data_dir)
    marker = root / DONE_MARKER
    if marker.exists() and not force:
        log.info("%s already available in %s", release.name, root)
        return root

    root.mkdir(parents=True, exist_ok=True)
    bundle = root / release.zenodo_file
    if not bundle.exists() or force:
        url, checksum = zenodo_file_info(release.zenodo_record, release.zenodo_file)
        _download(url, bundle, checksum)

    archive = archive_dir(release, data_dir)
    if archive.exists():
        shutil.rmtree(archive)
    with zipfile.ZipFile(bundle) as zf:
        zf.extractall(archive)

    irfs = irf_dir(release, data_dir)
    irfs.mkdir(exist_ok=True)
    tarballs = sorted(archive.rglob("*.tar.gz"))
    for tb in tarballs:
        with tarfile.open(tb) as tf:
            for member in tf.getmembers():
                if member.isfile() and member.name.endswith((".fits", ".fits.gz")):
                    member.name = Path(member.name).name  # flatten
                    tf.extract(member, irfs, filter="data")
        tb.unlink()  # the extracted FITS files are all we need

    n = len(list(irfs.glob("*.fits*")))
    log.info("%s: %d IRF files from %d tarballs", release.name, n, len(tarballs))
    bundle.unlink()
    marker.write_text(f"{n}\n")
    return root


def wanted_root_files(release: Release) -> set[str]:
    """Names of the ROOT files the figures use: default azimuth and sky condition,
    every site, zenith angle and optimisation time of the release."""
    return {
        release.root_irf_filename(site, duration, zenith=zenith)
        for site in release.sites
        for zenith in release.zeniths
        for duration in release.durations.values()
    }


def fetch_root(release: Release, data_dir, force=False) -> Path:
    """Download the Zenodo bundle with the ROOT files and keep the ones the figures need.

    The bundle is about 1 GB; only :func:`wanted_root_files` are extracted, into
    ``<data_dir>/<name>/root``. The tarballs are read straight from the zip.
    """
    if not release.zenodo_root_file:
        raise ValueError(f"{release.name} has no `zenodo.root_file` in its YAML")
    root = release_dir(release, data_dir)
    out = root_dir(release, data_dir)
    marker = root / ROOT_DONE_MARKER
    if marker.exists() and not force:
        log.info("%s ROOT files already available in %s", release.name, out)
        return out

    root.mkdir(parents=True, exist_ok=True)
    bundle = root / release.zenodo_root_file
    if not bundle.exists() or force:
        url, checksum = zenodo_file_info(release.zenodo_record, release.zenodo_root_file)
        _download(url, bundle, checksum)

    wanted = wanted_root_files(release)
    out.mkdir(exist_ok=True)
    found = set()
    with zipfile.ZipFile(bundle) as zf:
        for info in zf.infolist():
            if not info.filename.endswith(".tar.gz") or "root" not in info.filename.lower():
                continue
            with zf.open(info) as raw, tarfile.open(fileobj=raw, mode="r|gz") as tf:
                for member in tf:
                    name = Path(member.name).name
                    if member.isfile() and name in wanted:
                        member.name = name
                        tf.extract(member, out, filter="data")
                        found.add(name)
    missing = wanted - found
    if missing:
        log.warning("%s: %d expected ROOT files not in the bundle, e.g. %s",
                    release.name, len(missing), sorted(missing)[0])
    log.info("%s: %d ROOT files extracted to %s", release.name, len(found), out)
    bundle.unlink()
    marker.write_text(f"{len(found)}\n")
    return out
