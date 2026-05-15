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
- Get sold to a third party — see [SECURITY.md](#security) for why this matters

## Verifying the build

_Reproducible build pipeline lands in v1.0 release. When it does:_

1. Clone at the tagged release commit.
2. Run the build script.
3. Compare the resulting `dist/` SHA-256 against the hash published in the GitHub release notes.
4. Compare both against the SHA-256 of the `.zip` Chrome Web Store distributes.

All three must match. If they don't, something is wrong — open an issue.

## AVIF

AVIF is **not** supported in v1.0. Chrome's `OffscreenCanvas.convertToBlob` doesn't reliably encode AVIF in mid-2026, and bundling a WebAssembly encoder would add ~500 KB of code that users would also have to audit. AVIF returns in v1.1 once the platform encoder is stable, or as an explicit optional add-on.

## Contributing

Issues and PRs welcome. Two non-negotiable rules for contributors:

1. **No network calls** other than `fetch()` against the image URL the user right-clicked.
2. **No runtime dependencies** that load remote code or initialize SDKs.

Anything that compromises the trust positioning will be closed.

## Security

If you find a vulnerability or anything sketchy, please open an issue (or, for sensitive disclosures, contact via the address on the GitHub profile). Do not include exploits in public issues; we'll set up a private channel.

If you're ever offered the extension for sale: **don't sell**. That's exactly how the previous one got hijacked.

## License

[MIT](LICENSE) — do anything you want, just don't pretend you wrote it.
