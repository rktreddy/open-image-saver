# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**Open Image Saver** — Manifest V3 Chrome extension that adds a right-click "Save image as → PNG/JPG/WebP" submenu. Rebuild of an extension that was hijacked for affiliate fraud in March 2026, so **trust positioning is the entire product** — see the README for the user-facing pitch and permissions table.

**AVIF is deferred to v1.1.** Chrome's `OffscreenCanvas.convertToBlob` doesn't reliably encode AVIF as of mid-2026, and bundling a WASM encoder would inflate the audit surface. The menu intentionally has no AVIF item in v1.0.

## Non-Negotiable Constraints

These break the product if violated, regardless of how convenient they look:

- **No telemetry, analytics, or error reporting.** No Sentry, no Google Analytics, no ping-home. Ever.
- **No affiliate links, no monetization gates on core features, no account system, no cloud sync.**
- **No runtime dependencies that fetch remote code or call out.** Anything bundled must be auditable and offline-only (e.g. a WASM encoder for AVIF is OK; an SDK that initializes a network client is not).
- **Reproducible builds matter.** Don't introduce non-deterministic build steps (timestamps in output, network fetches at build time, unpinned versions).
- **Don't rename the extension to "Save Image as Type" verbatim** — Web Store similar-name policy.

If a change might compromise any of the above, surface it explicitly before writing code.

## Build, Run, Test

There is **no build step, no package manager, no test runner** at this stage. Files are loaded directly as an unpacked extension.

- **Load:** `chrome://extensions` → enable Developer mode → "Load unpacked" → pick the repo root.
- **Reload after edits:** click the circular reload arrow on the extension's card in `chrome://extensions`. The context menu only re-registers on `chrome.runtime.onInstalled`, which fires on reload from this UI.
- **Service worker logs:** on the extension's card, click the "service worker" link → opens DevTools for `background.js`. The worker terminates after ~30s idle; clicking the link wakes it.
- **Offscreen document logs:** the offscreen document doesn't show up in `chrome://extensions`. Inspect it via `chrome://inspect/#other` once it's been created.

A build/test pipeline arrives in Week 4 (reproducible build + SHA-256 publish). Don't add tooling earlier than that without a reason — the trust story is easier to verify when the source tree is the build.

## Architecture

Four execution contexts. The first three are the live save pipeline (`chrome.runtime` messaging between them); the fourth is settings-only.

1. **Service worker (`background.js`)** — registers the context menu on `onInstalled`, receives the click, reads user settings from `chrome.storage.local`, ensures the offscreen document exists, asks it to convert the image, then calls `chrome.downloads.download` on the returned blob URL and tells offscreen to revoke it once the download leaves `in_progress`. Stateless across wake cycles — anything that must persist goes in `chrome.storage.local`.
2. **Offscreen document (`offscreen.html` + `offscreen.js`)** — exists because service workers can't touch `document`, `Image`, or `<canvas>`. Fetches the image bytes (offscreen documents inherit `<all_urls>` host permission, so cross-origin works), enforces a 50 MB source-size cap, decodes via `createImageBitmap`, draws to `OffscreenCanvas`, calls `convertToBlob({ type, quality })`, and returns a blob URL string. The offscreen doc owns the blob URL lifecycle — the SW can't receive a Blob across `chrome.runtime.sendMessage` (JSON-only serialization), so URL strings are the contract.
3. **Content script (`content.js`, not yet present)** — only added if a real site breaks the `info.srcUrl` path (e.g. CSS `background-image`, `<picture>`/`<source>` resolution, lazy-load shims that hide the real URL). Default to solving in the worker; reach for a content script only when forced.
4. **Popup (`popup.html` + `popup.js`)** — settings UI only, not on the save path. Reads/writes `chrome.storage.local` directly. Three keys: `saveAs` (boolean), `quality` (60 | 80 | 100, sent to offscreen as a 0–1 float), `defaultFormat` ("png" | "jpg" | "webp" — stored but not yet read by the menu; reserved for future features like reordering or a top-level "Save image" action).

The popup never talks to the SW or offscreen directly. Settings flow popup → storage → SW on next click. That ordering is intentional: it means popup logic can't accidentally trigger a save.

## Permissions Discipline

Every permission in `manifest.json` is justified in the README's "Permissions, and why each is needed" table and in the Web Store listing copy. Don't add a new permission without updating both — reviewers and skeptical users read them. In particular, do not introduce `tabs`, `activeTab`, `scripting`, `cookies`, or `webRequest` unless a specific feature genuinely requires it.
