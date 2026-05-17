#!/usr/bin/env python3
"""Deterministic packager for the Open Image Saver extension.

Produces dist/open-image-saver-v{version}.zip with byte-reproducible output:
uncompressed (ZIP_STORED) entries, pinned timestamps, sorted member order.
Run twice and the archive is identical. Verification flow: see the README
"Verifying the build" section.
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

# Pinned Zip entry metadata. Any fixed values work; these maximize portability.
FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)  # minimum the DOS date field allows
CREATE_SYSTEM_MSDOS = 0  # MS-DOS: carries no Unix permission bits

# Exact runtime file set shipped to the Chrome Web Store. Explicit, not derived
# from manifest.json: offscreen.html is loaded at runtime via
# chrome.offscreen.createDocument and never appears in the manifest.
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
    # compression=ZIP_STORED applies to all entries; no per-entry override needed.
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        for rel in sorted(ALLOWLIST):
            info = zipfile.ZipInfo(filename=rel, date_time=FIXED_DATE_TIME)
            info.create_system = CREATE_SYSTEM_MSDOS
            info.external_attr = 0
            zf.writestr(info, (root / rel).read_bytes())
            # CPython's _open_to_write() overwrites a falsy external_attr with
            # 0o600<<16 (Unix permission bits). Re-zero via the ZipInfo already
            # appended to zf.filelist — mutating `info` after writestr has no
            # effect, since writestr's internal copy is what landed in filelist.
            zf.filelist[-1].external_attr = 0
    return zip_path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str], root: Path | None = None) -> int:
    root = root or Path(__file__).resolve().parent

    expect_version = None
    args = argv[1:]
    if args and args[0] == "--expect-version":
        if len(args) < 2:
            print("error: --expect-version requires a value", file=sys.stderr)
            return 2
        expect_version = args[1]

    missing = find_missing(root)
    if missing:
        print("error: missing required files:", file=sys.stderr)
        for rel in missing:
            print(f"  {rel}", file=sys.stderr)
        return 1

    version = read_version(root)
    if expect_version is not None and version != expect_version:
        print(
            f"error: manifest version {version!r} does not match "
            f"expected {expect_version!r}",
            file=sys.stderr,
        )
        return 1

    zip_path = build_zip(root, root / "dist", version)
    print(f"built:  {zip_path.relative_to(root)}")
    print(f"sha256: {sha256(zip_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
