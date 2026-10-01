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
