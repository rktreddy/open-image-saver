# Open Image Saver

Right-click any image on any webpage and save it as **PNG**, **JPG**, or **WebP**.

Open source. No telemetry. No analytics. No affiliate links. No account. Ever.

## Why this exists

In March 2026, the popular "Save Image as Type" extension was pulled from the Chrome Web Store after its new owners injected affiliate-fraud code. Roughly a million users were left without a working replacement.

This extension is a clean-room rebuild with one principle: **everything that touches your browser must be auditable**. The source is right here. The build is reproducible (see [Verifying the build](#verifying-the-build)). No code phones home.

## Install

- **Chrome Web Store:** _link will appear here when v1.0 is approved_
- **Sideload from source:** clone this repo, then in Chrome open `chrome://extensions`, enable Developer mode, click "Load unpacked", and pick the repo root.

## How it works

Right-click any image → **Save image as** → pick a format. The image downloads in that format.

Settings (toolbar icon → popup):
- **Ask where to save each image** — toggle Chrome's "Save As…" dialog
- **JPG / WebP quality** — 60% / 80% / 100%
- **Default format** — stored preference (used in future features)

## Permissions, and why each is needed

| Permission | Why |
|---|---|
| `contextMenus` | Add the right-click "Save image as" submenu |
| `downloads` | Save the converted image to your downloads folder |
| `offscreen` | Run `OffscreenCanvas` for the actual format conversion. MV3 service workers can't access `canvas`, so the work happens in an offscreen document |
| `storage` | Remember your settings (quality, default format, save-as toggle) |
| `<all_urls>` host permission | Fetch the image you right-clicked. Cross-origin images need this, otherwise the extension can't read the bytes. **No data is sent anywhere** — the image is fetched, converted locally, and downloaded |

If you want to confirm the host permission isn't being abused, search the repo for `fetch(` — every call site is in `offscreen.js` and the URL comes directly from the image you right-clicked.

## What this extension will never do

- Track you (no analytics, no error reporting services, no ping-home)
- Inject affiliate links or coupon-finder overlays
- Add a "premium tier" gate on core functionality
- Sync to the cloud
- Add an account system
- Get sold to a third party — see [SECURITY.md](SECURITY.md) for why this matters

## Verifying the build

Every tagged release publishes the SHA-256 of the distributed `.zip`. The build
is reproducible — anyone can regenerate the exact same archive from source:

1. `git clone https://github.com/rktreddy/open-image-saver && cd open-image-saver`
2. `git checkout <tag>` — the release tag you want to verify (e.g. `v1.0.0`)
3. `python3 pack.py`
4. Compare the hex digest on the printed `sha256:` line against the hash in that release's notes (the notes show the raw hex).

A match proves the released artifact was built from exactly this source, with no
hidden step. Verifying needs only `git` and `python3` — no other tools.

Note: this verifies the **uploaded `.zip`**, not the installed extension. The
Chrome Web Store repacks every upload into its own signed `.crx`, so the file
Chrome serves is never byte-identical to the `.zip` — that is true of every
extension on the store. What is verifiable, and what this guarantees, is that
the release artifact is faithfully reproducible from the public source.

## AVIF

AVIF is **not** supported in v1.0. Chrome's `OffscreenCanvas.convertToBlob` doesn't reliably encode AVIF in mid-2026, and bundling a WebAssembly encoder would add ~500 KB of code that users would also have to audit. AVIF returns in v1.1 once the platform encoder is stable, or as an explicit optional add-on.

## Contributing

Issues and PRs welcome. Two non-negotiable rules for contributors:

1. **No network calls** other than `fetch()` against the image URL the user right-clicked.
2. **No runtime dependencies** that load remote code or initialize SDKs.

Anything that compromises the trust positioning will be closed.

## Security

See [SECURITY.md](SECURITY.md) for the full policy: how to report a vulnerability privately, what's in and out of scope, response targets, and the maintainer commitments (including the "this project will not be sold" pledge — the previous extension was hijacked exactly because its maintainer sold it).

## License

[MIT](LICENSE) — do anything you want, just don't pretend you wrote it.
