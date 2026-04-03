/**
 * speclib Spectral Library Browser
 *
 * Plotly.js interactive spectral viewer integrated into docs site.
 * Loads pre-built JSON catalog, supports search/filter, and renders
 * interactive reflectance plots with zoom, pan, crosshair readout,
 * continuum removal, spectral derivatives, band math, and convolution.
 */

/* global Plotly */
/* eslint-env browser */

const SL = (() => {
  "use strict";

  const MAX_OVERLAY = 6;

  const PALETTE = [
    ["#1a56db", "solid",   "circle"],
    ["#dc2626", "dash",    "square"],
    ["#16a34a", "dot",     "diamond"],
    ["#d97706", "dashdot", "triangle-up"],
    ["#7c3aed", "longdash","cross"],
    ["#0891b2", "longdashdot","x"],
  ];

  const SENSOR_BANDS = {
    landsat: {
      name: "Landsat 8/9 OLI",
      bands: [
        { label: "Coastal", center: 0.443, width: 0.016, color: "rgba(100,100,255,0.12)" },
        { label: "Blue",    center: 0.482, width: 0.060, color: "rgba(0,0,220,0.10)" },
        { label: "Green",   center: 0.561, width: 0.057, color: "rgba(0,180,0,0.10)" },
        { label: "Red",     center: 0.655, width: 0.037, color: "rgba(220,0,0,0.10)" },
        { label: "NIR",     center: 0.865, width: 0.028, color: "rgba(150,0,0,0.10)" },
        { label: "SWIR1",   center: 1.609, width: 0.085, color: "rgba(180,120,0,0.10)" },
        { label: "SWIR2",   center: 2.201, width: 0.187, color: "rgba(120,80,0,0.10)" },
      ]
    },
    sentinel: {
      name: "Sentinel-2 MSI",
      bands: [
        { label: "B2",  center: 0.490, width: 0.065, color: "rgba(0,0,220,0.10)" },
        { label: "B3",  center: 0.560, width: 0.035, color: "rgba(0,180,0,0.10)" },
        { label: "B4",  center: 0.665, width: 0.030, color: "rgba(220,0,0,0.10)" },
        { label: "B8",  center: 0.842, width: 0.115, color: "rgba(140,0,0,0.10)" },
        { label: "B11", center: 1.610, width: 0.090, color: "rgba(180,120,0,0.10)" },
        { label: "B12", center: 2.190, width: 0.180, color: "rgba(120,80,0,0.10)" },
      ]
    }
  };

  const ABSORPTIONS = [
    { wl: 0.43,  label: "Fe\u00B3\u207A" },
    { wl: 0.55,  label: "Fe\u00B2\u207A" },
    { wl: 0.67,  label: "Chl" },
    { wl: 1.4,   label: "H\u2082O/OH" },
    { wl: 1.9,   label: "H\u2082O" },
    { wl: 2.2,   label: "Al-OH" },
    { wl: 2.35,  label: "CO\u2083" },
  ];

  const BAND_INDICES = {
    NDVI: { nir: 0.865, red: 0.655 },
    NDWI: { green: 0.56, nir: 0.865 },
    EVI:  { nir: 0.865, red: 0.655, blue: 0.48 },
  };

  // Build absolute data URL from the current page location
  const DATA_URL = (() => {
    const path = window.location.pathname;
    const root = path.replace(/\/library\/(index\.html)?$/, "/");
    return window.location.origin + root + "data/";
  })();

  // State
  let catalog = null;
  let filtered = [];
  let loaded = [];    // { id, name, wl, refl }
  let viewMode = "reflectance";
  let showLandsat = false;
  let showSentinel = false;
  let showAbsorptions = false;
  let showConvolve = false;
  let chartReady = false;

  const chartEl = () => document.getElementById("sl-chart");

  // ========== SPECTRAL TRANSFORMS ==========

  function computeContinuum(wl, refl) {
    const n = wl.length;
    if (n < 3) return refl.slice();
    const hull = [0];
    for (let i = 1; i < n; i++) {
      while (hull.length >= 2) {
        const a = hull[hull.length - 2], b = hull[hull.length - 1];
        if ((wl[b] - wl[a]) * (refl[i] - refl[a]) - (refl[b] - refl[a]) * (wl[i] - wl[a]) >= 0) hull.pop();
        else break;
      }
      hull.push(i);
    }
    const cont = new Float64Array(n);
    let hi = 0;
    for (let i = 0; i < n; i++) {
      while (hi < hull.length - 1 && wl[i] > wl[hull[hi + 1]]) hi++;
      const a = hull[hi], b = hull[Math.min(hi + 1, hull.length - 1)];
      cont[i] = a === b ? refl[a] : refl[a] + ((wl[i] - wl[a]) / (wl[b] - wl[a])) * (refl[b] - refl[a]);
    }
    return Array.from(cont).map((c, i) => c > 0.001 ? refl[i] / c : 1.0);
  }

  function computeDerivative(wl, refl, order) {
    let dw = [], dr = [];
    for (let i = 1; i < wl.length - 1; i++) {
      const span = wl[i + 1] - wl[i - 1];
      if (span > 0) { dw.push(wl[i]); dr.push((refl[i + 1] - refl[i - 1]) / span); }
    }
    if (order === 2 && dw.length > 2) {
      const dw2 = [], dr2 = [];
      for (let i = 1; i < dw.length - 1; i++) {
        const span = dw[i + 1] - dw[i - 1];
        if (span > 0) { dw2.push(dw[i]); dr2.push((dr[i + 1] - dr[i - 1]) / span); }
      }
      return { wl: dw2, refl: dr2 };
    }
    return { wl: dw, refl: dr };
  }

  function interpAt(wl, refl, target) {
    for (let i = 0; i < wl.length - 1; i++) {
      if (wl[i] <= target && wl[i + 1] >= target) {
        const t = (target - wl[i]) / (wl[i + 1] - wl[i]);
        return refl[i] + t * (refl[i + 1] - refl[i]);
      }
    }
    return null;
  }

  function convolveBands(wl, refl, sensorKey) {
    const sensor = SENSOR_BANDS[sensorKey];
    if (!sensor) return [];
    return sensor.bands.map(b => {
      const sigma = b.width / 2.355;
      let sw = 0, swr = 0;
      for (let i = 0; i < wl.length; i++) {
        const w = Math.exp(-0.5 * ((wl[i] - b.center) / sigma) ** 2);
        sw += w; swr += w * refl[i];
      }
      return sw > 0 ? { label: b.label, center: b.center, value: swr / sw } : null;
    }).filter(Boolean);
  }

  function computeGroupStats() {
    if (loaded.length < 2) return null;
    let lo = -Infinity, hi = Infinity;
    for (const s of loaded) { lo = Math.max(lo, s.wl[0]); hi = Math.min(hi, s.wl[s.wl.length - 1]); }
    if (lo >= hi) return null;
    const grid = loaded[0].wl.filter(w => w >= lo && w <= hi);
    if (grid.length < 10) return null;
    const all = loaded.map(s => grid.map(g => interpAt(s.wl, s.refl, g) || 0));
    const mean = grid.map((_, j) => all.reduce((s, r) => s + r[j], 0) / all.length);
    const std = grid.map((_, j) => {
      const m = mean[j];
      return Math.sqrt(all.reduce((s, r) => s + (r[j] - m) ** 2, 0) / all.length);
    });
    return { wl: grid, mean, upper: mean.map((m, i) => m + std[i]), lower: mean.map((m, i) => m - std[i]) };
  }

  // ========== CHART ==========

  function getYLabel() {
    const labels = { reflectance: "Reflectance", continuum: "Continuum-Removed", derivative1: "dR/d\u03BB", derivative2: "d\u00B2R/d\u03BB\u00B2" };
    return labels[viewMode] || "Reflectance";
  }

  function buildLayout() {
    const shapes = [], annotations = [];

    if (viewMode === "reflectance" || viewMode === "continuum") {
      const addBands = (sensor, show) => {
        if (!show) return;
        for (const b of sensor.bands) {
          shapes.push({ type: "rect", xref: "x", yref: "paper", x0: b.center - b.width / 2, x1: b.center + b.width / 2, y0: 0, y1: 1, fillcolor: b.color, line: { width: 0 }, layer: "below" });
          annotations.push({ x: b.center, y: 1.02, xref: "x", yref: "paper", text: b.label, showarrow: false, font: { size: 8 } });
        }
      };
      addBands(SENSOR_BANDS.landsat, showLandsat);
      addBands(SENSOR_BANDS.sentinel, showSentinel);
    }

    if (showAbsorptions) {
      for (const a of ABSORPTIONS) {
        shapes.push({ type: "line", xref: "x", yref: "paper", x0: a.wl, x1: a.wl, y0: 0, y1: 0.92, line: { color: "#888", width: 1, dash: "dot" }, layer: "below" });
        annotations.push({ x: a.wl, y: 0.95, xref: "x", yref: "paper", text: a.label, showarrow: false, font: { size: 7 }, textangle: -45 });
      }
    }

    return {
      xaxis: { title: "Wavelength (\u00B5m)", tickformat: ".2f", hoverformat: ".4f" },
      yaxis: { title: getYLabel(), tickformat: ".3f", hoverformat: ".4f", range: viewMode === "reflectance" ? [-0.02, 1.05] : undefined },
      margin: { l: 60, r: 15, t: 10, b: 45 },
      hovermode: "x unified", dragmode: "zoom", showlegend: false,
      shapes, annotations,
    };
  }

  function renderChart() {
    const el = chartEl();
    if (!el) return;

    const traces = [];
    for (let i = 0; i < loaded.length; i++) {
      const s = loaded[i];
      const [color, dash, symbol] = PALETTE[i];
      let x, y;

      if (viewMode === "continuum") { x = s.wl; y = computeContinuum(s.wl, s.refl); }
      else if (viewMode === "derivative1") { const d = computeDerivative(s.wl, s.refl, 1); x = d.wl; y = d.refl; }
      else if (viewMode === "derivative2") { const d = computeDerivative(s.wl, s.refl, 2); x = d.wl; y = d.refl; }
      else { x = s.wl; y = s.refl; }

      traces.push({
        x, y, type: "scattergl", mode: "lines", name: s.name,
        line: { color, width: 1.5, dash },
        hovertemplate: `<b>${s.name}</b><br>%{x:.4f} \u00B5m<br>${getYLabel()}: %{y:.4f}<extra></extra>`,
      });

      if (showConvolve && viewMode === "reflectance") {
        for (const [key, show] of [["landsat", showLandsat], ["sentinel", showSentinel]]) {
          if (!show) continue;
          const conv = convolveBands(s.wl, s.refl, key);
          traces.push({
            x: conv.map(c => c.center), y: conv.map(c => c.value),
            type: "scatter", mode: "markers", name: `${s.name} (${key})`,
            marker: { color, size: 9, symbol, line: { width: 1.5, color: "#fff" } },
            text: conv.map(c => c.label),
            hovertemplate: "<b>%{text}</b><br>%{x:.3f} \u00B5m<br>Convolved: %{y:.4f}<extra></extra>",
            showlegend: false,
          });
        }
      }
    }

    if (chartReady) {
      Plotly.react(el, traces, buildLayout(), { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["select2d", "lasso2d"] });
    } else {
      Plotly.newPlot(el, traces, buildLayout(), { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["select2d", "lasso2d"] });
      chartReady = true;
    }
  }

  function addGroupStats() {
    const stats = computeGroupStats();
    if (!stats) return;
    const el = chartEl();
    if (!el) return;
    Plotly.addTraces(el, [
      { x: [...stats.wl, ...stats.wl.slice().reverse()], y: [...stats.upper, ...stats.lower.slice().reverse()], fill: "toself", fillcolor: "rgba(26,86,219,0.12)", line: { color: "transparent" }, type: "scatter", mode: "lines", name: "\u00B11\u03C3", hoverinfo: "skip" },
      { x: stats.wl, y: stats.mean, type: "scatter", mode: "lines", name: `Mean (n=${loaded.length})`, line: { color: "#1a56db", width: 2.5 }, hovertemplate: "<b>Mean</b><br>%{x:.4f} \u00B5m<br>R: %{y:.4f}<extra></extra>" },
    ]);
  }

  function showIndices() {
    const panel = document.getElementById("sl-indices-panel");
    if (!panel || loaded.length === 0) { if (panel) panel.style.display = "none"; return; }
    let html = "";
    for (let i = 0; i < loaded.length; i++) {
      const s = loaded[i];
      const nir = interpAt(s.wl, s.refl, 0.865), red = interpAt(s.wl, s.refl, 0.655);
      const green = interpAt(s.wl, s.refl, 0.56), blue = interpAt(s.wl, s.refl, 0.48);
      const ndvi = nir !== null && red !== null && (nir + red) !== 0 ? ((nir - red) / (nir + red)).toFixed(3) : "N/A";
      const ndwi = green !== null && nir !== null && (green + nir) !== 0 ? ((green - nir) / (green + nir)).toFixed(3) : "N/A";
      let evi = "N/A";
      if (nir !== null && red !== null && blue !== null) {
        const d = nir + 6 * red - 7.5 * blue + 1;
        if (d !== 0) evi = (2.5 * (nir - red) / d).toFixed(3);
      }
      html += `<div style="margin:0.25rem 0;font-size:0.82rem"><span style="color:${PALETTE[i][0]}; font-weight:600">${s.name}</span> &mdash; NDVI: <code>${ndvi}</code> NDWI: <code>${ndwi}</code> EVI: <code>${evi}</code></div>`;
    }
    panel.innerHTML = html;
    panel.style.display = "block";
  }

  function downloadCSV() {
    if (loaded.length === 0) return;
    let csv = "wavelength_um";
    for (const s of loaded) csv += `,${s.name.replace(/,/g, ";")}`;
    csv += "\n";
    const ref = loaded[0];
    for (let i = 0; i < ref.wl.length; i++) {
      csv += ref.wl[i];
      for (const s of loaded) csv += `,${s.refl[i] !== undefined ? s.refl[i] : ""}`;
      csv += "\n";
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `speclib_export_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function downloadPNG() {
    const el = chartEl();
    if (!el || !chartReady) return;
    Plotly.downloadImage(el, { format: "png", filename: `speclib_chart_${Date.now()}`, width: 1600, height: 800, scale: 2 });
  }

  // ========== CATALOG & TABLE ==========

  async function fetchCatalog() {
    try {
      const resp = await fetch(DATA_URL + "catalog.json");
      if (!resp.ok) { showEmpty("Catalog not found. Run the build pipeline first."); return; }
      catalog = await resp.json();
      filtered = catalog.spectra;
      populateFilters();
      renderTable();
      updateCount();
    } catch {
      showEmpty("Failed to load catalog.");
    }
  }

  function populateFilters() {
    if (!catalog) return;
    const cats = new Set(), sources = new Set(), quals = new Set();
    for (const s of catalog.spectra) { cats.add(s.category); sources.add(s.source); quals.add(s.quality); }
    fillSelect("sl-filter-category", [...cats].sort(), "All Categories");
    fillSelect("sl-filter-source", [...sources].sort(), "All Sources");
    fillSelect("sl-filter-quality", [...quals].sort(), "All Quality");
  }

  function fillSelect(id, values, allLabel) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `<option value="">${allLabel}</option>` + values.map(v => `<option value="${v}">${v}</option>`).join("");
  }

  function applyFilters() {
    if (!catalog) return;
    const query = (document.getElementById("sl-search")?.value || "").toLowerCase();
    const cat = document.getElementById("sl-filter-category")?.value || "";
    const src = document.getElementById("sl-filter-source")?.value || "";
    const qual = document.getElementById("sl-filter-quality")?.value || "";

    filtered = catalog.spectra.filter(s => {
      if (query) {
        const hay = `${s.name} ${s.category} ${s.source}`.toLowerCase();
        if (!query.split(/\s+/).every(t => hay.includes(t))) return false;
      }
      if (cat && s.category !== cat) return false;
      if (src && s.source !== src) return false;
      if (qual && s.quality !== qual) return false;
      return true;
    });
    renderTable();
    updateCount();
  }

  function updateCount() {
    const el = document.getElementById("sl-result-count");
    if (el) el.textContent = `${filtered.length} spectra`;
  }

  function renderTable() {
    const tbody = document.getElementById("sl-results-body");
    if (!tbody) return;
    if (filtered.length === 0) { tbody.innerHTML = '<tr><td colspan="5" class="sl-empty">No matching spectra</td></tr>'; return; }

    tbody.innerHTML = "";
    for (const s of filtered.slice(0, 200)) {
      const tr = document.createElement("tr");
      tr.dataset.id = s.id;
      tr.innerHTML = `<td title="${s.name}">${truncate(s.name, 35)}</td><td>${s.category}</td><td>${s.source}</td><td>${s.n_bands}</td><td>${s.wl_min.toFixed(2)}\u2013${s.wl_max.toFixed(2)}</td>`;
      tr.addEventListener("click", () => onSpectrumClick(s));
      tbody.appendChild(tr);
    }
  }

  // ========== SPECTRUM LOADING ==========

  async function onSpectrumClick(catalogEntry) {
    if (loaded.length >= MAX_OVERLAY) loaded.shift();
    if (loaded.some(l => l.id === catalogEntry.id)) { showMetadata(catalogEntry); return; }

    try {
      const resp = await fetch(DATA_URL + `spectra/${catalogEntry.id}.json`);
      if (!resp.ok) return;
      const data = await resp.json();

      const wl = [], refl = [];
      for (let i = 0; i < data.wavelengths.length; i++) {
        const w = data.wavelengths[i], r = data.reflectance[i];
        if (w != null && r != null && isFinite(w) && isFinite(r)) { wl.push(w); refl.push(r); }
      }

      loaded.push({ id: data.id, name: data.name, wl, refl });
      renderChart();
      showMetadata(catalogEntry);
      highlightRow(catalogEntry.id);
    } catch (err) {
      console.error("Error loading spectrum:", err);
    }
  }

  function clearSpectra() {
    loaded = [];
    viewMode = "reflectance";
    const vm = document.getElementById("sl-view-mode");
    if (vm) vm.value = "reflectance";
    const panel = document.getElementById("sl-indices-panel");
    if (panel) panel.style.display = "none";
    renderChart();
    const meta = document.getElementById("sl-metadata");
    if (meta) meta.innerHTML = '<h3>Spectrum Details</h3><p class="sl-hint">Click a spectrum in the table to view it</p>';
    document.querySelectorAll("#sl-results-body tr.sl-selected").forEach(tr => tr.classList.remove("sl-selected"));
  }

  function highlightRow(id) {
    document.querySelectorAll("#sl-results-body tr.sl-selected").forEach(tr => tr.classList.remove("sl-selected"));
    const row = document.querySelector(`#sl-results-body tr[data-id="${id}"]`);
    if (row) row.classList.add("sl-selected");
  }

  function showMetadata(s) {
    const panel = document.getElementById("sl-metadata");
    if (!panel) return;
    panel.innerHTML = `
      <h3>${truncate(s.name, 50)}</h3>
      <div class="sl-meta-grid">
        <span class="sl-meta-label">Category</span><span class="sl-meta-value">${s.category}</span>
        <span class="sl-meta-label">Source</span><span class="sl-meta-value">${s.source}</span>
        <span class="sl-meta-label">Quality</span><span class="sl-meta-value">${s.quality}</span>
        <span class="sl-meta-label">Bands</span><span class="sl-meta-value">${s.n_bands}</span>
        <span class="sl-meta-label">Range</span><span class="sl-meta-value">${s.wl_min.toFixed(3)}\u2013${s.wl_max.toFixed(3)} \u00b5m</span>
        <span class="sl-meta-label">Instrument</span><span class="sl-meta-value">${s.instrument || "\u2014"}</span>
        <span class="sl-meta-label">License</span><span class="sl-meta-value">${s.license || "\u2014"}</span>
      </div>
      <div style="margin-top:0.75rem">
        <a href="${DATA_URL}spectra/${s.id}.json" download style="font-size:0.78rem">Download JSON</a>
      </div>
    `;
  }

  // ========== EVENTS ==========

  function setupEventListeners() {
    const bind = (id, event, fn) => { const el = document.getElementById(id); if (el) el.addEventListener(event, fn); };

    bind("sl-search", "input", debounce(applyFilters, 200));
    bind("sl-filter-category", "change", applyFilters);
    bind("sl-filter-source", "change", applyFilters);
    bind("sl-filter-quality", "change", applyFilters);
    bind("sl-view-mode", "change", (e) => { viewMode = e.target.value; renderChart(); });
    bind("sl-toggle-landsat", "change", (e) => { showLandsat = e.target.checked; renderChart(); });
    bind("sl-toggle-sentinel", "change", (e) => { showSentinel = e.target.checked; renderChart(); });
    bind("sl-toggle-absorptions", "change", (e) => { showAbsorptions = e.target.checked; renderChart(); });
    bind("sl-toggle-convolve", "change", (e) => { showConvolve = e.target.checked; renderChart(); });
    bind("sl-btn-stats", "click", addGroupStats);
    bind("sl-btn-indices", "click", showIndices);
    bind("sl-btn-reset-zoom", "click", () => { const el = chartEl(); if (el) Plotly.relayout(el, { "xaxis.autorange": true, "yaxis.autorange": true }); });
    bind("sl-btn-clear", "click", clearSpectra);
    bind("sl-btn-csv", "click", downloadCSV);
    bind("sl-btn-png", "click", downloadPNG);
  }

  // ========== UTILITIES ==========

  function truncate(str, len) { return str.length > len ? str.slice(0, len) + "\u2026" : str; }
  function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
  function showEmpty(msg) { const el = document.getElementById("sl-results-body"); if (el) el.innerHTML = `<tr><td colspan="5" class="sl-empty">${msg}</td></tr>`; }

  // ========== INIT ==========

  function init() {
    fetchCatalog();
    setupEventListeners();
    renderChart();
  }

  return { init };
})();

// Initialize: try multiple strategies since load timing varies
if (typeof document$ !== "undefined") {
  document$.subscribe(() => { if (document.getElementById("sl-chart")) SL.init(); });
} else if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => { if (document.getElementById("sl-chart")) SL.init(); });
} else {
  if (document.getElementById("sl-chart")) SL.init();
}
