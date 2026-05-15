const MENU_PARENT_ID = "save-image-as";
const OFFSCREEN_URL = "offscreen.html";

// AVIF deferred to v1.1 — Chrome OffscreenCanvas AVIF encoder isn't reliably
// available as of mid-2026, and bundling a WASM encoder would inflate the
// audit surface (PROJECT.md trust positioning).
const FORMATS = [
  { id: "png", label: "PNG" },
  { id: "jpg", label: "JPG" },
  { id: "webp", label: "WebP" }
];

const DEFAULT_SETTINGS = {
  quality: 80,          // applied as quality/100 to JPG/WebP encoding
  saveAs: false,        // chrome.downloads.download saveAs
  defaultFormat: "png"  // stored for future features; not yet read by the menu
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_PARENT_ID,
      title: "Save image as",
      contexts: ["image"]
    });

    for (const fmt of FORMATS) {
      chrome.contextMenus.create({
        id: `${MENU_PARENT_ID}:${fmt.id}`,
        parentId: MENU_PARENT_ID,
        title: fmt.label,
        contexts: ["image"]
      });
    }
  });
});

chrome.contextMenus.onClicked.addListener((info) => {
  if (typeof info.menuItemId !== "string") return;
  if (!info.menuItemId.startsWith(`${MENU_PARENT_ID}:`)) return;
  if (!info.srcUrl) return;

  const format = info.menuItemId.split(":")[1];
  if (!FORMATS.some((f) => f.id === format)) return;

  saveImage(info.srcUrl, format).catch((err) => {
    console.error("[open-image-saver] failed:", err);
  });
});

async function saveImage(srcUrl, format) {
  const settings = await getSettings();
  await ensureOffscreen();

  const response = await chrome.runtime.sendMessage({
    target: "offscreen",
    action: "convert",
    src: srcUrl,
    format,
    quality: settings.quality / 100
  });

  if (!response?.ok) {
    throw new Error(response?.error || "convert failed");
  }

  const filename = deriveFilename(srcUrl, format);
  const downloadId = await chrome.downloads.download({
    url: response.url,
    filename,
    saveAs: settings.saveAs
  });

  const onChanged = (delta) => {
    if (delta.id !== downloadId) return;
    if (delta.state?.current && delta.state.current !== "in_progress") {
      chrome.downloads.onChanged.removeListener(onChanged);
      chrome.runtime.sendMessage({
        target: "offscreen",
        action: "revoke",
        url: response.url
      });
    }
  };
  chrome.downloads.onChanged.addListener(onChanged);
}

async function getSettings() {
  return chrome.storage.local.get(DEFAULT_SETTINGS);
}

async function ensureOffscreen() {
  const exists = await chrome.offscreen.hasDocument();
  if (exists) return;
  await chrome.offscreen.createDocument({
    url: OFFSCREEN_URL,
    reasons: ["BLOBS"],
    justification: "Encode images to PNG/JPG/WebP via OffscreenCanvas"
  });
}

const ILLEGAL_FILENAME_CHARS = /[\\\/:*?"<>|\x00-\x1f]/g;

function deriveFilename(srcUrl, format) {
  const ext = format;
  if (srcUrl.startsWith("data:") || srcUrl.startsWith("blob:")) {
    return `image-${Date.now()}.${ext}`;
  }
  try {
    const u = new URL(srcUrl);
    const last = u.pathname.split("/").filter(Boolean).pop() ?? "";
    let stem;
    try { stem = decodeURIComponent(last); } catch { stem = last; }
    stem = stem.replace(/\.[^.]+$/, "");
    stem = stem.replace(ILLEGAL_FILENAME_CHARS, "_").trim();
    stem = stem.replace(/^\.+/, "").replace(/\.+$/, "");
    if (stem) return `${stem}.${ext}`;
  } catch {}
  return `image-${Date.now()}.${ext}`;
}
