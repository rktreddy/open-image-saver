const MIME = {
  png: "image/png",
  jpg: "image/jpeg",
  webp: "image/webp"
};

const MAX_SRC_BYTES = 50 * 1024 * 1024;

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.target !== "offscreen") return;

  if (msg.action === "convert") {
    convert(msg.src, msg.format, msg.quality)
      .then((url) => sendResponse({ ok: true, url }))
      .catch((err) => sendResponse({ ok: false, error: String(err?.message || err) }));
    return true;
  }

  if (msg.action === "revoke") {
    try { URL.revokeObjectURL(msg.url); } catch {}
    sendResponse({ ok: true });
    return false;
  }
});

async function convert(src, format, quality) {
  const mime = MIME[format];
  if (!mime) throw new Error(`unsupported format: ${format}`);

  const res = await fetch(src);
  if (!res.ok) throw new Error(`fetch ${res.status}`);
  const srcBlob = await res.blob();
  if (srcBlob.size > MAX_SRC_BYTES) {
    throw new Error(`source image too large: ${srcBlob.size} bytes`);
  }

  let bitmap;
  try {
    bitmap = await createImageBitmap(srcBlob);
  } catch (e) {
    throw new Error(`decode failed: ${e?.message || e}`);
  }

  const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("no 2d context");
  ctx.drawImage(bitmap, 0, 0);
  bitmap.close();

  const opts = { type: mime };
  if (format === "jpg" || format === "webp") {
    opts.quality = typeof quality === "number" ? quality : 0.8;
  }

  const outBlob = await canvas.convertToBlob(opts);
  return URL.createObjectURL(outBlob);
}
