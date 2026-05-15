const DEFAULTS = { quality: 80, saveAs: false, defaultFormat: "png" };

const els = {
  saveAs: document.getElementById("saveAs"),
  defaultFormat: document.getElementById("defaultFormat"),
  qualityInputs: () => document.querySelectorAll('input[name="quality"]')
};

async function load() {
  const s = await chrome.storage.local.get(DEFAULTS);
  els.saveAs.checked = !!s.saveAs;
  els.defaultFormat.value = s.defaultFormat;
  for (const r of els.qualityInputs()) {
    r.checked = Number(r.value) === s.quality;
  }
}

function save(patch) {
  return chrome.storage.local.set(patch);
}

document.addEventListener("DOMContentLoaded", () => {
  load();

  els.saveAs.addEventListener("change", () => {
    save({ saveAs: els.saveAs.checked });
  });

  els.defaultFormat.addEventListener("change", () => {
    save({ defaultFormat: els.defaultFormat.value });
  });

  for (const r of els.qualityInputs()) {
    r.addEventListener("change", () => {
      if (r.checked) save({ quality: Number(r.value) });
    });
  }
});
