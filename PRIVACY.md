# Privacy Policy — Open Image Saver

**Effective date:** May 18, 2026

## The short version

Open Image Saver collects nothing, sends nothing anywhere, and has no servers.
There is no account, no telemetry, no analytics, no tracking. This page explains
exactly what the extension does — and does not do — with data.

## What the extension does

When you right-click an image and choose a format, the extension:

1. **Fetches the image you selected** — from the website that already hosts it,
   the same place your browser loaded it from. This network request goes to that
   image's host, never to the developer.
2. **Converts it locally**, inside your own browser, using an offscreen canvas.
   The image is not uploaded anywhere to be converted.
3. **Saves the result** to your computer's Downloads folder.

That is the entire data flow. The conversion happens entirely on your machine.

## What is stored

Your settings — default format, JPG/WebP quality, and the "ask where to save"
toggle — are stored using `chrome.storage.local`. That means they live on your
computer only. They are not synced to a Google account and are never transmitted
anywhere.

Nothing else is stored. The extension keeps no history or record of the images
you save.

## What is NOT collected

To be explicit, the extension does not collect, store, or transmit any of:

- Personal or identifying information
- Browsing history, or the pages you visit
- The images you save, or any record of them
- Analytics, usage statistics, or telemetry of any kind
- Crash reports or error reports

There is no analytics service, no error-reporting service, and no
developer-controlled server involved at any point.

## Permissions, and why each exists

- **`contextMenus`** — to add the right-click "Save image as" menu.
- **`downloads`** — to save the converted image to your Downloads folder.
- **`offscreen`** — to run the image conversion (a Manifest V3 service worker
  cannot use a canvas directly).
- **`storage`** — to remember your settings, on your device.
- **`<all_urls>` host permission** — so the extension can fetch the image you
  right-click. Images are often hosted on a different domain than the page
  they appear on; without this permission the extension could not read them.
  It is used only to retrieve the specific image you choose to save — never in
  the background, never on a schedule, never on pages you have not acted on.

## Third parties

There are none. No third-party services, SDKs, analytics, or advertising are
included in this extension. It has never contained affiliate links and never
will.

## Open source

The complete source code is public at
https://github.com/rktreddy/open-image-saver. Every claim on this page can be
verified by reading it — the extension makes exactly one kind of network
request, and you can find it by searching the code for `fetch(`.

## Changes to this policy

If the extension's data behavior ever changes, this policy will be updated, the
effective date above will change, and the change will be described in the
release notes for the version that introduces it.

## Contact

Questions about privacy can be raised as an issue on the GitHub repository, or
sent to the email address on the maintainer's GitHub profile
(https://github.com/rktreddy).
