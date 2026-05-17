import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pack


def make_fixture(root: Path, version: str = "1.2.3") -> None:
    """Write a complete fake extension tree into `root`."""
    manifest = {
        "manifest_version": 3,
        "name": "Open Image Saver",
        "version": version,
    }
    (root / "manifest.json").write_text(json.dumps(manifest))
    for name in [
        "background.js",
        "offscreen.html",
        "offscreen.js",
        "popup.html",
        "popup.js",
        "LICENSE",
    ]:
        (root / name).write_text(f"content of {name}\n")
    icons = root / "icons"
    icons.mkdir()
    for size in [16, 32, 48, 128]:
        (icons / f"{size}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([size]))


class ReadVersionTest(unittest.TestCase):
    def test_reads_version_from_manifest(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root, version="9.9.9")
            self.assertEqual(pack.read_version(root), "9.9.9")


class FindMissingTest(unittest.TestCase):
    def test_all_present_returns_empty(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            self.assertEqual(pack.find_missing(root), [])

    def test_missing_file_is_reported(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            (root / "icons" / "48.png").unlink()
            self.assertEqual(pack.find_missing(root), ["icons/48.png"])


if __name__ == "__main__":
    unittest.main()
