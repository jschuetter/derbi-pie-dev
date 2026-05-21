/* DERBi PIE keyboard (JSON-driven) */

async function loadKeyboardJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load keyboard JSON (${res.status}): ${url}`);
  return await res.json();
}

/* Modifier composition maps */
const APPLY = {
  acute: { k: "ḱ", g: "ǵ", s: "ś" },
  underdot: { t: "ṭ", d: "ḍ", n: "ṇ", r: "ṛ", l: "ḷ", s: "ṣ" },
  macron: { a: "ā", e: "ē", i: "ī", o: "ō", u: "ū" },
  syllabic: { r: "r̥", l: "l̥", m: "m̥", n: "n̥" },
  glide: { i: "i̯", u: "u̯" },
  aspiration: { b: "bʰ", d: "dʰ", g: "gʰ", "gʷ": "gʷʰ", ǵ: "ǵʰ" },
  labialization: { k: "kʷ", g: "gʷ" },
  sub1: { h: "h₁" },
  sub2: { h: "h₂" },
  sub3: { h: "h₃" }
};

const COMBINING = {
  acute: "\u0301",
  underdot: "\u0323",
  macron: "\u0304",
  syllabic: "\u0325",
  glide: "\u032F"
};

const APPEND = {
  aspiration: "ʰ",
  labialization: "ʷ"
};

function mergeAllFamilies(familiesByLang) {
  const merged = {};
  for (const lang of Object.keys(familiesByLang)) {
    const fam = familiesByLang[lang];
    for (const base of Object.keys(fam)) {
      const b = base.replace(/[0-9]+$/, "");
      merged[b] = merged[b] || [];
      for (const ch of fam[base]) if (!merged[b].includes(ch)) merged[b].push(ch);
    }
  }
  return merged;
}

/* Treat gʷ as one unit */
function getTargetSymbol(textLeft) {
  const m = textLeft.match(/(.)(ʷ)?$/u);
  return m ? m[0] : null;
}

function insertAtCaret(input, text) {
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? input.value.length;
  input.value = input.value.slice(0, start) + text + input.value.slice(end);
  const newPos = start + text.length;
  input.setSelectionRange(newPos, newPos);
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.focus();
}

function applyModifierToInput(inputEl, key) {
  const start = inputEl.selectionStart ?? inputEl.value.length;
  const end = inputEl.selectionEnd ?? inputEl.value.length;
  const text = inputEl.value;

  let left = text.slice(0, start);
  let right = text.slice(end);
  let target = "";

  if (start !== end) {
    const sel = text.slice(start, end);
    const t = getTargetSymbol(sel);
    if (!t) return false;
    target = t;
    left = text.slice(0, start) + sel.slice(0, sel.length - target.length);
  } else {
    const t = getTargetSymbol(left);
    if (!t) return false;
    target = t;
    left = left.slice(0, left.length - target.length);
  }

  const map = APPLY[key] || {};
  const replacement = map[target] || map[target.normalize("NFD")[0]];

  if (replacement) {
    inputEl.value = left + replacement + right;
    const pos = left.length + replacement.length;
    inputEl.setSelectionRange(pos, pos);
    inputEl.dispatchEvent(new Event("input", { bubbles: true }));
    inputEl.focus();
    return true;
  }

  if (COMBINING[key]) {
    inputEl.value = left + target + COMBINING[key] + right;
    const pos = (left + target + COMBINING[key]).length;
    inputEl.setSelectionRange(pos, pos);
    inputEl.dispatchEvent(new Event("input", { bubbles: true }));
    inputEl.focus();
    return true;
  }

  if (APPEND[key]) {
    inputEl.value = left + target + APPEND[key] + right;
    const pos = (left + target + APPEND[key]).length;
    inputEl.setSelectionRange(pos, pos);
    inputEl.dispatchEvent(new Event("input", { bubbles: true }));
    inputEl.focus();
    return true;
  }

  return false;
}

function updateModifierAvailability(inputEl) {
  const text = inputEl.value;
  const start = inputEl.selectionStart ?? text.length;
  const end = inputEl.selectionEnd ?? text.length;

  let symbol = null;
  if (start !== end) symbol = getTargetSymbol(text.slice(start, end));
  else symbol = getTargetSymbol(text.slice(0, start));

  const base = symbol ? symbol.normalize("NFD")[0] : null;

  document.querySelectorAll(".mod").forEach(btn => {
    const key = btn.dataset.mod;
    btn.disabled = false;

    if (!symbol) { btn.disabled = true; return; }

    if (key.startsWith("sub")) { btn.disabled = (base !== "h"); return; }
    if (key === "macron") { btn.disabled = !(/[aeiou]/.test(base)); return; }
    if (key === "syllabic") { btn.disabled = !(/[rlmn]/.test(base)); return; }
    if (key === "glide") { btn.disabled = !(/[iu]/.test(base)); return; }
    if (key === "labialization") { btn.disabled = !(/[kg]/.test(base)); return; }
    if (key === "aspiration") { btn.disabled = !(/[bdgkpt]/.test(base) || symbol === "gʷ" || base === "ǵ"); return; }
    if (key === "acute") { btn.disabled = !(/[kgs]/.test(base)); return; }
    if (key === "underdot") { btn.disabled = !(/[tdnrls]/.test(base)); return; }
  });
}

export async function mountDerbiKeyboard(rootEl, { dataUrl }) {
  const data = await loadKeyboardJson(dataUrl);

  const meta = data.meta || {};
  const familiesByLangRaw = data.familiesByLang || {};

  // Inject "all" mode if missing
  const familiesByLang = { ...familiesByLangRaw };
  if (!familiesByLang.all) familiesByLang.all = mergeAllFamilies(familiesByLang);

  // Build UI skeleton inside rootEl
  rootEl.innerHTML = `
    <div class="wrap">
      <div class="search-row">
        <input id="search" type="text" placeholder="Search… (click ⌨ for symbols)" autocomplete="off" />
        <button id="kbToggle" type="button" aria-expanded="false" title="Show / hide symbol keyboard">⌨</button>
      </div>

      <div id="kbPanel" hidden>
        <div class="subtle" style="margin-bottom:10px;">
          Click symbols to insert. Then click modifiers to adjust the previous symbol (or a selection).
        </div>

        <div id="baseGrid" class="base-grid" aria-label="Base keys"></div>

        <div class="row" aria-label="Variants">
          <div id="activeLabel" class="label">–</div>
          <div id="variantStrip" class="variant-strip"></div>
        </div>

        <div class="mods" id="modifiers">
          <div class="mods-head">
            <strong>Modifiers</strong>
            <span class="subtle">Apply to previous symbol (or selection)</span>
          </div>

          <div class="mods-row">
            <button class="mod" data-mod="acute">X́</button>
            <button class="mod" data-mod="underdot">X̣</button>
            <button class="mod" data-mod="macron">X̄</button>
            <button class="mod" data-mod="syllabic">X̥</button>
            <button class="mod" data-mod="glide">X̯</button>
            <button class="mod" data-mod="aspiration" title="Aspiration">ʰ</button>
            <button class="mod" data-mod="labialization" title="Labialization">ʷ</button>
            <button class="mod" data-mod="sub1" title="Subscript 1">₁</button>
            <button class="mod" data-mod="sub2" title="Subscript 2">₂</button>
            <button class="mod" data-mod="sub3" title="Subscript 3">₃</button>
          </div>

          <div class="subtle" style="margin-top:8px;">
            Last modifier: <span id="lastModLabel">none</span> (double-click in the search box to reapply)
          </div>

          <div style="margin-top:14px; border-top:1px solid #ddd; padding-top:12px;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
              <strong>Language</strong>
              <span class="subtle">Filters the keyboard symbols</span>
            </div>

            <div style="margin-top:8px; display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
              <label for="langSelect" class="subtle" style="font-weight:600;">Mode:</label>
              <select id="langSelect"
                      style="padding:8px 10px; border:1px solid #bbb; border-radius:10px; background:#fff;"></select>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Wire DOM
  const searchEl = rootEl.querySelector("#search");
  const kbToggle = rootEl.querySelector("#kbToggle");
  const kbPanel  = rootEl.querySelector("#kbPanel");
  const baseGrid = rootEl.querySelector("#baseGrid");
  const activeLabel = rootEl.querySelector("#activeLabel");
  const variantStrip = rootEl.querySelector("#variantStrip");
  const lastModLabel = rootEl.querySelector("#lastModLabel");
  const langSelect = rootEl.querySelector("#langSelect");

  // Populate language dropdown from JSON meta (fallback if missing)
  const langs = meta.languages || Object.keys(familiesByLang).map(id => ({ id, label: id }));
  langSelect.innerHTML = "";
  for (const lang of langs) {
    const opt = document.createElement("option");
    opt.value = lang.id;
    opt.textContent = lang.label;
    langSelect.appendChild(opt);
  }

  let currentLang = meta.defaultLang || "pie";
  if (!familiesByLang[currentLang]) currentLang = "pie";
  langSelect.value = currentLang;

  function getFamilies() {
    const src = familiesByLang[currentLang] || familiesByLang.pie;
    const out = {};
    for (const key of Object.keys(src)) {
      const base = key.replace(/[0-9]+$/, "");
      out[base] = out[base] || [];
      for (const ch of src[key]) if (!out[base].includes(ch)) out[base].push(ch);
    }
    return out;
  }

  let activeBase = Object.keys(getFamilies()).sort()[0];
  let lastModKey = null;

  function setKeyboardOpen(open) {
    kbPanel.hidden = !open;
    kbToggle.setAttribute("aria-expanded", String(open));
    if (open) searchEl.focus();
  }
  kbToggle.addEventListener("click", () => setKeyboardOpen(kbPanel.hidden));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !kbPanel.hidden) setKeyboardOpen(false);
  });

  function renderBaseGrid() {
    const families = getFamilies();
    const bases = Object.keys(families).sort();
    baseGrid.innerHTML = "";
    bases.forEach(base => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "base-btn" + (base === activeBase ? " active" : "");
      btn.textContent = base;
      btn.addEventListener("click", () => {
        activeBase = base;
        renderBaseGrid();
        renderVariants();
        searchEl.focus();
      });
      baseGrid.appendChild(btn);
    });
  }

  function renderVariants() {
    const families = getFamilies();
    const variants = families[activeBase] || [];
    activeLabel.textContent = activeBase;
    variantStrip.innerHTML = "";
    variants.forEach(ch => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "key-btn";
      btn.textContent = ch;
      btn.addEventListener("click", () => {
        insertAtCaret(searchEl, ch);
        updateModifierAvailability(searchEl);
      });
      variantStrip.appendChild(btn);
    });
  }

  function setLastMod(key) {
    lastModKey = key;
    lastModLabel.textContent = key || "none";
    rootEl.querySelectorAll(".mod").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.mod === key);
    });
  }

  rootEl.querySelectorAll(".mod").forEach(btn => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      const key = btn.dataset.mod;
      const ok = applyModifierToInput(searchEl, key);
      if (ok) {
        setLastMod(key);
        updateModifierAvailability(searchEl);
      }
    });
  });

  ["input","click","keyup"].forEach(ev =>
    searchEl.addEventListener(ev, () => updateModifierAvailability(searchEl))
  );

  searchEl.addEventListener("dblclick", () => {
    if (!lastModKey) return;
    const btn = rootEl.querySelector(`.mod[data-mod="${lastModKey}"]`);
    if (btn && btn.disabled) return;
    applyModifierToInput(searchEl, lastModKey);
    updateModifierAvailability(searchEl);
  });

  langSelect.addEventListener("change", () => {
    currentLang = langSelect.value;
    const families = getFamilies();
    if (!families[activeBase]) activeBase = Object.keys(families).sort()[0];
    renderBaseGrid();
    renderVariants();
    updateModifierAvailability(searchEl);
    searchEl.focus();
  });

  // Init
  renderBaseGrid();
  renderVariants();
  updateModifierAvailability(searchEl);
}
