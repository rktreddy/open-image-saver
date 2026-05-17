# Reproducible Build Pipeline — Design

**Date:** 2026-05-16
**Project:** Open Image Saver (MV3 Chrome extension)
**Status:** Approved for planning

## Problem

The README and `SECURITY.md` promise that a published release can be verified
against the source. No build pipeline exists yet, and the current docs make a
claim that is not literally achievable (see "Docs corrections" below). This
design defines a pipeline that produces a byte-deterministic extension package
and a verification flow a skeptic can actually follow.

## Goals

- A published `.zip` is **reproducible**: anyone who clones the tagged source
  and runs the build gets a byte-identical archive with a matching SHA-256.
- Verification requires only tools a developer already has: `git` + `python3`.
- The trust chain is as short as possible — no bundler, no `npm install`, no
  `uv`, no third-party build action beyond `actions/checkout`.

## Non-goals (YAGNI)

- No minification, bundling, or transpilation. Shipped files must stay
  byte-identical to the repo files so "audit the code" stays literally true.
- No source maps.
- No PR/push build checks — the workflow runs only on release tags.
- No `.crx` generation. The Chrome Web Store repacks and signs the upload; the
  pipeline stops at the `.zip`.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Build tool | Single `pack.py`, Python stdlib only | Nothing to bundle; zero installed dependencies to audit |
| Compression | `ZIP_STORED` (uncompressed) | Eliminates zlib as a nondeterminism source — no version pinning needed |
| Python management | System `python3`, no `uv` | With `ZIP_STORED` there is no interpreter-dependent output; `uv` would add a tool to the verifier's chain for no benefit |
| Where the build runs | GitHub Actions on `v*` tag push | Public build log removes "did the maintainer hand-edit the zip" from the threat model |
| Verification claim | Reproducibility only | The Web Store distributes a repacked, signed `.crx`, never the uploaded `.zip` — a zip-hash comparison against the store download is impossible |

## Architecture

### `pack.py` (repo root, Python stdlib only)

The entire build. Steps:

1. Read `version` from `manifest.json`.
2. Validate every file on the allowlist exists. If any are missing, print the
   missing list and exit non-zero.
3. Write `dist/open-image-saver-v{version}.zip` using `ZIP_STORED`. For each
   member, construct a `ZipInfo` explicitly with these pinned values (any
   fixed values work; these are chosen for maximum portability):
   - members added in sorted (byte-wise) path order
   - `date_time = (1980, 1, 1, 0, 0, 0)` — the minimum the DOS date field can
     represent, so it is identical on every platform
   - `create_system = 0` — MS-DOS, which carries no Unix permission bits
   - `external_attr = 0` — no permission/attribute metadata
   - `compress_type = ZIP_STORED`
4. Compute the SHA-256 of the finished zip and print it to stdout.

`pack.py` is idempotent — a second run produces a byte-identical archive.

No `build.sh`: once `pack.py` does its own validation and hashing, a shell
wrapper is a no-op `exec python3 pack.py`. The single entry point is
`python3 pack.py`.

### Allowlist

Hardcoded in `pack.py`. The exact runtime file set:

- `manifest.json`
- `background.js`
- `offscreen.html`
- `offscreen.js`
- `popup.html`
- `popup.js`
- `icons/16.png`, `icons/32.png`, `icons/48.png`, `icons/128.png`
- `LICENSE`

Excluded: `README.md`, `CLAUDE.md`, `SECURITY.md`, `PROJECT.md`, `.gitignore`,
`pack.py`, `.github/`, `docs/`.

The allowlist is **not** derived from `manifest.json`: `offscreen.html` is
loaded at runtime via `chrome.offscreen.createDocument` and never appears in
the manifest, so an explicit list is the only correct source of truth.

### `.github/workflows/release.yml`

- **Trigger:** push of a tag matching `v*`.
- **Permissions:** `contents: write` (needed to create a release).
- **Steps:**
  1. Checkout (`actions/checkout`, SHA-pinned).
  2. Assert the git tag (`v1.0.0`) matches `manifest.json`'s `version`
     (`1.0.0`). On mismatch, fail before creating a release.
  3. `python3 pack.py`.
  4. `gh release create` with the `.zip` attached and the SHA-256 in the
     release body.
- The only third-party action is `actions/checkout`. Release creation uses the
  `gh` CLI (preinstalled on runners) in a plain `run` step, keeping the
  workflow fully auditable.

## Trust property

Because there is no minification or bundling, the files inside the package are
byte-identical to the repo files — the "build" is effectively `copy + zip`. The
reproducible-build machinery exists only to make the zip *wrapper*
deterministic, not to verify a code transformation. Verification therefore
reduces to: "confirm the zip faithfully contains the source you are already
reading."

## Verification flow

Documented in README and `SECURITY.md`:

1. `git clone … && git checkout v1.0.0`
2. `python3 pack.py`
3. Compare the printed SHA-256 against the hash in the v1.0.0 GitHub Release
   notes.

A match proves the released artifact came from exactly this source with no
hidden step. Required tools: `git` and `python3` only.

## Docs corrections (in scope)

Both the README "Verifying the build" section and the `SECURITY.md` "Verifying
a release" section currently imply comparison against the Web Store `.zip`.
That is not achievable — Google repacks the upload into a signed `.crx`. Both
sections are rewritten to state the reproducibility-only claim and the concrete
`python3 pack.py` command.

## Failure handling

- **Missing allowlisted file** (e.g. icons not yet created): `pack.py` exits
  non-zero with the missing list. This will fail until the Week 3 icons exist
  and are re-added to `manifest.json` — intended behavior; never silently ship
  a partial package.
- **Tag/version mismatch:** the workflow fails before any release is created.
- **Idempotency:** running `pack.py` twice yields a byte-identical zip.

## Dependency on other work

The build will not succeed until the icon set (`icons/16.png`, `32.png`,
`48.png`, `128.png`) exists and `manifest.json` references it again. Icons are
a separate Week 3 task. The pipeline can be built and committed before then;
its first successful run is gated on the icons landing.
