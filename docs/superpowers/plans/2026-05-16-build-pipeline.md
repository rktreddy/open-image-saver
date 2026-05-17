# Reproducible Build Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic packaging pipeline that produces a byte-reproducible extension `.zip` with a verifiable SHA-256, published automatically on release tags.

**Architecture:** A single stdlib-only `pack.py` validates an explicit file allowlist, writes an uncompressed (`ZIP_STORED`) archive with pinned entry metadata, and prints its SHA-256. A tag-triggered GitHub Actions workflow runs `pack.py` and publishes the zip + hash to a GitHub Release. Tests use Python's `unittest` (no third-party test runner).

**Tech Stack:** Python 3 standard library (`zipfile`, `hashlib`, `json`, `pathlib`, `unittest`), GitHub Actions, `gh` CLI.

---

## File Structure

- `pack.py` (repo root, create) — the entire build: allowlist validation, deterministic zip, SHA-256. Single responsibility: turn the source tree into a reproducible package.
- `test_pack.py` (repo root, create) — `unittest` tests for `pack.py`. Excluded from the package automatically (not on the allowlist).
- `.github/workflows/release.yml` (create) — tag-triggered release automation.
- `README.md` (modify) — rewrite the "Verifying the build" section.
- `SECURITY.md` (modify) — rewrite the "Verifying a release" section.
- `CLAUDE.md` (modify) — update the "Build, Run, Test" section, now that a build and test runner exist.

Spec reference: `docs/superpowers/specs/2026-05-16-build-pipeline-design.md`.

---

## Task 1: pack.py foundations — allowlist, version reading, missing-file detection

**Files:**
- Create: `pack.py`
- Create: `test_pack.py`

- [ ] **Step 1: Write the failing tests**

Create `test_pack.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_pack -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pack'`

- [ ] **Step 3: Write minimal implementation**

Create `pack.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_pack -v`
Expected: PASS — 3 tests OK

- [ ] **Step 5: Commit**

```bash
git add pack.py test_pack.py
git commit -m "Add pack.py allowlist, version reading, and missing-file check"
```

---

## Task 2: pack.py — deterministic zip builder

**Files:**
- Modify: `pack.py`
- Modify: `test_pack.py`

- [ ] **Step 1: Write the failing tests**

Append these test classes to `test_pack.py` (before the `if __name__` block):

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_pack -v`
Expected: FAIL — `AttributeError: module 'pack' has no attribute 'build_zip'`

- [ ] **Step 3: Write minimal implementation**

In `pack.py`, change the import line `import json` to:

```python
import json
import zipfile
```

Then add, after the `ALLOWLIST` list:

```python
# Pinned Zip entry metadata. Any fixed values work; these maximize portability.
FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)  # minimum the DOS date field allows
CREATE_SYSTEM_MSDOS = 0  # MS-DOS: carries no Unix permission bits
```

And add this function after `find_missing`:

```python
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
    return zip_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_pack -v`
Expected: PASS — 7 tests OK

- [ ] **Step 5: Commit**

```bash
git add pack.py test_pack.py
git commit -m "Add deterministic ZIP_STORED packer to pack.py"
```

---

## Task 3: pack.py — SHA-256 and the CLI entry point

**Files:**
- Modify: `pack.py`
- Modify: `test_pack.py`

- [ ] **Step 1: Write the failing tests**

Append these test classes to `test_pack.py` (before the `if __name__` block):

```python
import contextlib
import io


class Sha256Test(unittest.TestCase):
    def test_hash_is_stable_for_same_bytes(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            make_fixture(root)
            zip_path = pack.build_zip(root, root / "dist", "1.2.3")
            self.assertEqual(pack.sha256(zip_path), pack.sha256(zip_path))

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest test_pack -v`
Expected: FAIL — `AttributeError: module 'pack' has no attribute 'sha256'`

- [ ] **Step 3: Write minimal implementation**

In `pack.py`, change the imports block to:

```python
import hashlib
import json
import sys
import zipfile
from pathlib import Path
```

Add these two functions after `build_zip`:

```python
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
```

Add this block at the very end of `pack.py`:

```python
if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest test_pack -v`
Expected: PASS — 13 tests OK

- [ ] **Step 5: Commit**

```bash
git add pack.py test_pack.py
git commit -m "Add SHA-256 and CLI entry point to pack.py"
```

---

## Task 4: GitHub Actions release workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Resolve the pinned `actions/checkout` commit SHA**

Run: `gh api repos/actions/checkout/commits/v4 --jq .sha`
Expected: a 40-character hex SHA (for example `11bd71901bbe5b1630ceea73d27597364c9af683`). Use this value in place of `<CHECKOUT_SHA>` in the next step.

- [ ] **Step 2: Create the workflow file**

Create `.github/workflows/release.yml` (substitute the SHA from Step 1):

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@<CHECKOUT_SHA>  # v4

      - name: Build extension package
        run: python3 pack.py --expect-version "${GITHUB_REF_NAME#v}"

      - name: Publish release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          version="${GITHUB_REF_NAME#v}"
          zip="dist/open-image-saver-v${version}.zip"
          sha="$(sha256sum "$zip" | awk '{print $1}')"
          gh release create "$GITHUB_REF_NAME" "$zip" \
            --title "v${version}" \
            --notes "$(printf 'SHA-256 of `%s`:\n\n```\n%s\n```\n\nVerify: clone at this tag, run `python3 pack.py`, and compare the printed sha256.' "open-image-saver-v${version}.zip" "$sha")"
```

- [ ] **Step 3: Confirm the workflow file is in place**

Run: `test -f .github/workflows/release.yml && grep -q 'tags:' .github/workflows/release.yml && grep -q 'pack.py' .github/workflows/release.yml && echo "workflow OK"`
Expected: prints `workflow OK`

(There is no YAML parser in the Python stdlib; full validation happens when GitHub first ingests the file. This check confirms the file exists and contains the key directives.)

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Add tag-triggered release workflow"
```

---

## Task 5: Documentation corrections

**Files:**
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rewrite the README "Verifying the build" section**

In `README.md`, replace the entire `## Verifying the build` section (from its heading through the line ending `open an issue.`) with:

```markdown
## Verifying the build

Every tagged release publishes the SHA-256 of the distributed `.zip`. The build
is reproducible — anyone can regenerate the exact same archive from source:

1. `git clone https://github.com/rktreddy/open-image-saver && cd open-image-saver`
2. `git checkout v1.0.0` (the release tag you want to verify)
3. `python3 pack.py`
4. Compare the printed `sha256:` value against the hash in that release's notes.

A match proves the released artifact was built from exactly this source, with no
hidden step. Verifying needs only `git` and `python3` — no other tools.

Note: this verifies the **uploaded `.zip`**, not the installed extension. The
Chrome Web Store repacks every upload into its own signed `.crx`, so the file
Chrome serves is never byte-identical to the `.zip` — that is true of every
extension on the store. What is verifiable, and what this guarantees, is that
the release artifact is faithfully reproducible from the public source.
```

- [ ] **Step 2: Rewrite the SECURITY.md "Verifying a release" section**

In `SECURITY.md`, replace the entire `## Verifying a release` section (from its heading through the line ending `via the channels above.`) with:

```markdown
## Verifying a release

Each tagged release publishes the SHA-256 of the distributed `.zip`, and the
build is reproducible:

1. Clone the repository and `git checkout` the release tag.
2. Run `python3 pack.py`.
3. Compare the printed `sha256:` value against the hash in the release notes.

A match proves the release artifact was built from exactly the tagged source.
The build performs no minification or bundling — the files in the package are
byte-identical to the files in the repository — so the archive is simply a
faithful container of the source you can already read.

This verifies the uploaded `.zip`. It does not verify the installed `.crx`:
the Chrome Web Store repacks and re-signs every upload, so the served `.crx` is
never byte-identical to the `.zip`. A mismatch between a release's published
hash and a from-source rebuild is a security finding — please report it.
```

- [ ] **Step 3: Update the CLAUDE.md "Build, Run, Test" section**

In `CLAUDE.md`, replace the entire `## Build, Run, Test` section (from its heading through the paragraph ending `the source tree is the build.`) with:

```markdown
## Build, Run, Test

The extension loads directly as an unpacked extension — there is no bundler and
no transpilation. The "build" is packaging only.

- **Load:** `chrome://extensions` → enable Developer mode → "Load unpacked" → pick the repo root.
- **Reload after edits:** click the circular reload arrow on the extension's card in `chrome://extensions`. The context menu only re-registers on `chrome.runtime.onInstalled`, which fires on reload from this UI.
- **Service worker logs:** on the extension's card, click the "service worker" link → opens DevTools for `background.js`. The worker terminates after ~30s idle; clicking the link wakes it.
- **Offscreen document logs:** the offscreen document doesn't show up in `chrome://extensions`. Inspect it via `chrome://inspect/#other` once it's been created.
- **Build the package:** `python3 pack.py` → writes `dist/open-image-saver-v{version}.zip` and prints its SHA-256. Pure Python stdlib, no dependencies.
- **Run the tests:** `python3 -m unittest test_pack -v`. Uses stdlib `unittest`; no test-runner dependency.

The package is intentionally produced without minification so the shipped files
stay byte-identical to the repo files — "audit the code" must remain literally
true. See `pack.py` and `docs/superpowers/specs/2026-05-16-build-pipeline-design.md`.
```

- [ ] **Step 4: Commit**

```bash
git add README.md SECURITY.md CLAUDE.md
git commit -m "Correct build-verification docs to the reproducibility-only claim"
```

---

## Task 6: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `python3 -m unittest test_pack -v`
Expected: PASS — 13 tests OK

- [ ] **Step 2: Confirm pack.py fails loudly on the current (icon-less) tree**

Run: `python3 pack.py; echo "exit: $?"`
Expected: prints `error: missing required files:` listing `icons/16.png`, `icons/32.png`, `icons/48.png`, `icons/128.png`, then `exit: 1`.

This is correct behavior — the icons are a separate Week 3 task. The pipeline must refuse to ship a partial package. Once the icons exist and `manifest.json` references them again, `python3 pack.py` will succeed.

- [ ] **Step 3: Confirm a clean working tree**

Run: `git status --short`
Expected: empty output — everything committed.
