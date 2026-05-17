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


import zipfile


class BuildZipTest(unittest.TestCase):
    def test_zip_contains_exactly_allowlist(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            zip_path = pack.build_zip(root, root / "dist", "1.2.3")
            with zipfile.ZipFile(zip_path) as zf:
                self.assertEqual(sorted(zf.namelist()), sorted(pack.ALLOWLIST))

    def test_zip_filename_includes_version(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            zip_path = pack.build_zip(root, root / "dist", "4.5.6")
            self.assertEqual(zip_path.name, "open-image-saver-v4.5.6.zip")

    def test_entries_have_pinned_metadata(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            zip_path = pack.build_zip(root, root / "dist", "1.2.3")
            with zipfile.ZipFile(zip_path) as zf:
                for info in zf.infolist():
                    self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                    self.assertEqual(info.create_system, 0)
                    self.assertEqual(info.external_attr, 0)
                    self.assertEqual(info.compress_type, zipfile.ZIP_STORED)

    def test_build_is_deterministic(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            z1 = pack.build_zip(root, root / "out1", "1.2.3")
            z2 = pack.build_zip(root, root / "out2", "1.2.3")
            self.assertEqual(z1.read_bytes(), z2.read_bytes())


if __name__ == "__main__":
    unittest.main()
