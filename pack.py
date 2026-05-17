#!/usr/bin/env python3
"""Deterministic packager for the Open Image Saver extension.

Produces dist/open-image-saver-v{version}.zip with byte-reproducible output:
uncompressed (ZIP_STORED) entries, pinned timestamps, sorted member order.
Run twice and the archive is identical. Verification flow: see the README
"Verifying the build" section.
"""
import json
from pathlib import Path

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
