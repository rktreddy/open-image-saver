import contextlib
import io
import json
import unittest
import zipfile
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
        (icons / f"icon-{size}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([size]))


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
            (root / "icons" / "icon-48.png").unlink()
            self.assertEqual(pack.find_missing(root), ["icons/icon-48.png"])


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
                    self.assertEqual(info.date_time, pack.FIXED_DATE_TIME)
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


class Sha256Test(unittest.TestCase):
    def test_hash_is_stable_across_two_builds(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            z1 = pack.build_zip(root, root / "out1", "1.2.3")
            z2 = pack.build_zip(root, root / "out2", "1.2.3")
            self.assertEqual(pack.sha256(z1), pack.sha256(z2))

    def test_hash_is_64_hex_chars(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            zip_path = pack.build_zip(root, root / "dist", "1.2.3")
            digest = pack.sha256(zip_path)
            self.assertEqual(len(digest), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in digest))


class MainTest(unittest.TestCase):
    def _run(self, argv, root):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = pack.main(argv, root=root)
        return code, out.getvalue()

    def test_successful_build_exits_zero_and_writes_zip(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root, version="1.2.3")
            code, output = self._run(["pack.py"], root)
            self.assertEqual(code, 0)
            self.assertIn("sha256:", output)
            self.assertTrue((root / "dist" / "open-image-saver-v1.2.3.zip").is_file())

    def test_missing_files_exit_one(self):
        with TemporaryDirectory() as d:
            root = Path(d)  # empty: nothing on the allowlist exists
            code, output = self._run(["pack.py"], root)
            self.assertEqual(code, 1)
            self.assertIn("missing", output)

    def test_expect_version_match_exits_zero(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root, version="1.2.3")
            code, _ = self._run(["pack.py", "--expect-version", "1.2.3"], root)
            self.assertEqual(code, 0)

    def test_expect_version_mismatch_exits_one(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root, version="1.2.3")
            code, output = self._run(["pack.py", "--expect-version", "9.9.9"], root)
            self.assertEqual(code, 1)
            self.assertIn("9.9.9", output)

    def test_expect_version_missing_value_exits_two(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root, version="1.2.3")
            code, output = self._run(["pack.py", "--expect-version"], root)
            self.assertEqual(code, 2)
            self.assertIn("--expect-version", output)


if __name__ == "__main__":
    unittest.main()
