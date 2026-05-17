#!/usr/bin/env python3
"""Deterministic packager for the Open Image Saver extension.

Produces dist/open-image-saver-v{version}.zip with byte-reproducible output:
uncompressed (ZIP_STORED) entries, pinned timestamps, sorted member order.
Run twice and the archive is identical. Verification flow: see the README
"Verifying the build" section.
"""
import json
import zipfile
from pathlib import Path

# Exact runtime file set shipped to the Chrome Web Store. Explicit, not derived
# from manifest.json: offscreen.html is loaded at runtime via
# chrome.offscreen.createDocument and never appears in the manifest.
# Pinned Zip entry metadata. Any fixed values work; these maximize portability.
FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)  # minimum the DOS date field allows
CREATE_SYSTEM_MSDOS = 0  # MS-DOS: carries no Unix permission bits

ALLOWLIST = [
    "manifest.json",
    "background.js",
    "offscreen.html",
    "offscreen.js",
    "popup.html",
    "popup.js",
    "icons/16.png",
    "icons/32.png",
    "icons/48.png",
    "icons/128.png",
    "LICENSE",
]


def read_version(root: Path) -> str:
    manifest = json.loads((root / "manifest.json").read_text())
    return manifest["version"]


def find_missing(root: Path) -> list[str]:
    return [rel for rel in ALLOWLIST if not (root / rel).is_file()]


def build_zip(root: Path, out_dir: Path, version: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"open-image-saver-v{version}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for rel in sorted(ALLOWLIST):
            info = zipfile.ZipInfo(filename=rel, date_time=FIXED_DATE_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = CREATE_SYSTEM_MSDOS
            info.external_attr = 0
            zf.writestr(info, (root / rel).read_bytes())
            # _open_to_write() overwrites external_attr when it is falsy;
            # re-zero it on the recorded entry so the archive is portable.
            zf.filelist[-1].external_attr = 0
    return zip_path
