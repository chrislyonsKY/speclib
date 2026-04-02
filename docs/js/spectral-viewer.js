/**
 * speclib Spectral Library Browser
 *
 * D3.js v7 interactive spectral viewer integrated into Zensical docs.
 * Loads pre-built JSON catalog, supports search/filter, and renders
 * interactive reflectance plots with zoom, pan, and crosshair readout.
 */

/* global d3 */
/* eslint-env browser */

const SL = (() => {
  "use strict";

  const MAX_OVERLAY = 6;
  const LINE_CLASSES = ["sl-line-0", "sl-line-1", "sl-line-2", "sl-line-3", "sl-line-4", "sl-line-5"];
  // Build absolute data URL from the current page location
  const DATA_URL = (function () {
    const origin = window.location.origin;
    const path = window.location.pathname;
    // Strip /library/ or /library/index.html to get site root
    const root = path.replace(/\/library\/(index\.html)?$/, "/");
    return origin + root + "data/";
  })();

  let catalog = null;
  let filtered = [];
  let loaded = [];  // {id, name, wavelengths, reflectance}

  // Chart dimensions
  const margin = { top: 20, right: 20, bottom: 45, left: 55 };

  // Scales and axes (set on render)
  let svg, xScale, yScale, chartG, zoom;

  // ── Initialization ──────────────────────────────────────────────

  function init() {
    console.log("[speclib] init() called, DATA_URL =", DATA_URL);
    console.log("[speclib] d3 available:", typeof d3 !== "undefined");
    console.log("[speclib] #sl-chart:", document.getElementById("sl-chart"));
    fetchCatalog();
    setupEventListeners();
    setupChart();
    console.log("[speclib] setupChart done, svg:", svg ? "created" : "null");
  }

  async function fetchCatalog() {
    try {
      const resp = await fetch(DATA_URL + "catalog.json");
      if (!resp.ok) {
        showEmpty("Catalog not found. Run the build pipeline first.");
        return;
      }
      catalog = await resp.json();
      filtered = catalog.spectra;
      populateFilters();
      renderTable();
      updateCount();
    } catch {
      showEmpty("Failed to load catalog.");
    }
  }

  // ── Search & Filter ─────────────────────────────────────────────

  function setupEventListeners() {
    const searchEl = document.getElementById("sl-search");
    if (searchEl) {
      searchEl.addEventListener("input", debounce(applyFilters, 200));
    }
    for (const id of ["sl-filter-category", "sl-filter-source", "sl-filter-quality"]) {
      const el = document.getElementById(id);
      if (el) el.addEventListener("change", applyFilters);
    }
    const resetBtn = document.getElementById("sl-btn-reset-zoom");
    if (resetBtn) resetBtn.addEventListener("click", resetZoom);
    const clearBtn = document.getElementById("sl-btn-clear");
    if (clearBtn) clearBtn.addEventListener("click", clearSpectra);
  }

  function populateFilters() {
    if (!catalog) return;
    const cats = new Set(), sources = new Set(), quals = new Set();
    for (const s of catalog.spectra) {
      cats.add(s.category);
      sources.add(s.source);
      quals.add(s.quality);
    }
    fillSelect("sl-filter-category", [...cats].sort(), "All Categories");
    fillSelect("sl-filter-source", [...sources].sort(), "All Sources");
    fillSelect("sl-filter-quality", [...quals].sort(), "All Quality");
  }

  function fillSelect(id, values, allLabel) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `<option value="">${allLabel}</option>`;
    for (const v of values) {
      el.innerHTML += `<option value="${v}">${v}</option>`;
    }
  }

  function applyFilters() {
    if (!catalog) return;
    const query = (document.getElementById("sl-search")?.value || "").toLowerCase();
    const cat = document.getElementById("sl-filter-category")?.value || "";
    const src = document.getElementById("sl-filter-source")?.value || "";
    const qual = document.getElementById("sl-filter-quality")?.value || "";

    filtered = catalog.spectra.filter(s => {
      if (query && !s.name.toLowerCase().includes(query) && !s.material.toLowerCase().includes(query)) return false;
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

  // ── Results Table ───────────────────────────────────────────────

  function renderTable() {
    const tbody = document.getElementById("sl-results-body");
    if (!tbody) return;

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="sl-empty">No matching spectra</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    for (const s of filtered.slice(0, 200)) {
      const tr = document.createElement("tr");
      tr.dataset.id = s.id;
      tr.innerHTML = `
        <td title="${s.name}">${truncate(s.name, 35)}</td>
        <td>${s.category}</td>
        <td>${s.source}</td>
        <td>${s.n_bands}</td>
        <td>${s.wl_min.toFixed(2)}\u2013${s.wl_max.toFixed(2)}</td>
      `;
      tr.addEventListener("click", () => onSpectrumClick(s));
      tbody.appendChild(tr);
    }
  }

  // ── Spectrum Loading ────────────────────────────────────────────

  async function onSpectrumClick(catalogEntry) {
    console.log("[speclib] clicked:", catalogEntry.id, "svg:", !!svg, "chartG:", !!chartG);
    if (loaded.length >= MAX_OVERLAY) {
      loaded.shift();
    }

    // Check if already loaded
    if (loaded.some(l => l.id === catalogEntry.id)) {
      showMetadata(catalogEntry);
      return;
    }

    try {
      const url = DATA_URL + `spectra/${catalogEntry.id}.json`;
      const resp = await fetch(url);
      if (!resp.ok) {
        console.error("Failed to fetch spectrum:", url, resp.status);
        return;
      }
      const data = await resp.json();

      // Filter out NaN values for clean plotting
      const clean = { id: data.id, name: data.name, wavelengths: [], reflectance: [] };
      for (let i = 0; i < data.wavelengths.length; i++) {
        const w = data.wavelengths[i];
        const r = data.reflectance[i];
        if (isFinite(w) && isFinite(r)) {
          clean.wavelengths.push(w);
          clean.reflectance.push(r);
        }
      }

      loaded.push(clean);
      renderChart();
      showMetadata(catalogEntry);
      highlightRow(catalogEntry.id);
    } catch (err) {
      console.error("Error loading spectrum:", err);
    }
  }

  function clearSpectra() {
    loaded = [];
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

  // ── Metadata Panel ──────────────────────────────────────────────

  function showMetadata(s) {
    const panel = document.getElementById("sl-metadata");
    if (!panel) return;
    panel.innerHTML = `
      <h3>${truncate(s.name, 50)}</h3>
      <div class="sl-meta-grid">
        <span class="sl-meta-label">Material</span><span class="sl-meta-value">${s.material}</span>
        <span class="sl-meta-label">Category</span><span class="sl-meta-value">${s.category}</span>
        <span class="sl-meta-label">Source</span><span class="sl-meta-value">${s.source}</span>
        <span class="sl-meta-label">Quality</span><span class="sl-meta-value">${s.quality}</span>
        <span class="sl-meta-label">Bands</span><span class="sl-meta-value">${s.n_bands}</span>
        <span class="sl-meta-label">Range</span><span class="sl-meta-value">${s.wl_min.toFixed(3)}\u2013${s.wl_max.toFixed(3)} \u00b5m</span>
        <span class="sl-meta-label">Instrument</span><span class="sl-meta-value">${s.instrument || "\u2014"}</span>
        <span class="sl-meta-label">Locality</span><span class="sl-meta-value">${s.locality || "\u2014"}</span>
        <span class="sl-meta-label">License</span><span class="sl-meta-value">${s.license || "\u2014"}</span>
      </div>
      <div style="margin-top:0.75rem">
        <a href="${DATA_URL}spectra/${s.id}.json" download style="font-size:0.78rem">Download JSON</a>
      </div>
    `;
  }

  // ── D3.js Chart ─────────────────────────────────────────────────

  function setupChart() {
    const container = document.getElementById("sl-chart");
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 350;

    svg = d3.select(container)
      .append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    // Clip path
    svg.append("defs").append("clipPath")
      .attr("id", "sl-clip")
      .append("rect")
      .attr("x", margin.left)
      .attr("y", margin.top)
      .attr("width", width - margin.left - margin.right)
      .attr("height", height - margin.top - margin.bottom);

    chartG = svg.append("g").attr("clip-path", "url(#sl-clip)");

    // Default scales
    xScale = d3.scaleLinear().domain([0.35, 2.5]).range([margin.left, width - margin.right]);
    yScale = d3.scaleLinear().domain([0, 1]).range([height - margin.bottom, margin.top]);

    // Axes
    svg.append("g")
      .attr("class", "sl-axis sl-x-axis")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(xScale).ticks(10));

    svg.append("g")
      .attr("class", "sl-axis sl-y-axis")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(yScale).ticks(5));

    // Axis labels
    svg.append("text")
      .attr("class", "sl-axis-label")
      .attr("text-anchor", "middle")
      .attr("x", (width - margin.left - margin.right) / 2 + margin.left)
      .attr("y", height - 5)
      .text("Wavelength (\u00b5m)");

    svg.append("text")
      .attr("class", "sl-axis-label")
      .attr("text-anchor", "middle")
      .attr("transform", `rotate(-90)`)
      .attr("x", -(height - margin.top - margin.bottom) / 2 - margin.top)
      .attr("y", 14)
      .text("Reflectance");

    // Grid
    svg.append("g")
      .attr("class", "sl-grid")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(yScale).ticks(5).tickSize(-(width - margin.left - margin.right)).tickFormat(""));

    // Zoom
    zoom = d3.zoom()
      .scaleExtent([1, 20])
      .translateExtent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
      .extent([[margin.left, margin.top], [width - margin.right, height - margin.bottom]])
      .on("zoom", onZoom);

    svg.call(zoom);

    // Crosshair overlay
    const overlay = svg.append("rect")
      .attr("class", "sl-overlay")
      .attr("x", margin.left)
      .attr("y", margin.top)
      .attr("width", width - margin.left - margin.right)
      .attr("height", height - margin.top - margin.bottom)
      .attr("fill", "none")
      .attr("pointer-events", "all");

    const crosshairV = svg.append("line").attr("class", "sl-crosshair").attr("stroke", "#999").attr("stroke-dasharray", "3 3").style("display", "none");
    const crosshairH = svg.append("line").attr("class", "sl-crosshair").attr("stroke", "#999").attr("stroke-dasharray", "3 3").style("display", "none");

    overlay.on("mousemove", (event) => {
      const [mx, my] = d3.pointer(event);
      const wl = xScale.invert(mx);
      const refl = yScale.invert(my);

      crosshairV.style("display", null).attr("x1", mx).attr("x2", mx).attr("y1", margin.top).attr("y2", height - margin.bottom);
      crosshairH.style("display", null).attr("x1", margin.left).attr("x2", width - margin.right).attr("y1", my).attr("y2", my);

      const readout = document.getElementById("sl-crosshair-readout");
      if (readout) readout.textContent = `\u03bb ${wl.toFixed(4)} \u00b5m  |  R ${refl.toFixed(4)}`;
    });

    overlay.on("mouseleave", () => {
      crosshairV.style("display", "none");
      crosshairH.style("display", "none");
      const readout = document.getElementById("sl-crosshair-readout");
      if (readout) readout.textContent = "";
    });
  }

  function renderChart() {
    if (!chartG) return;
    chartG.selectAll("path.sl-spectrum-line").remove();

    if (loaded.length === 0) return;

    // Compute domain from loaded spectra
    let wlMin = Infinity, wlMax = -Infinity, rMax = 0;
    for (const s of loaded) {
      for (const w of s.wavelengths) { wlMin = Math.min(wlMin, w); wlMax = Math.max(wlMax, w); }
      for (const r of s.reflectance) { rMax = Math.max(rMax, r); }
    }

    xScale.domain([wlMin - 0.01, wlMax + 0.01]);
    yScale.domain([0, Math.min(1.05, rMax * 1.1)]);

    // Update axes
    const container = document.getElementById("sl-chart");
    const width = container ? container.clientWidth : 800;
    const height = container ? (container.clientHeight || 350) : 350;

    svg.select(".sl-x-axis").call(d3.axisBottom(xScale).ticks(10));
    svg.select(".sl-y-axis").call(d3.axisLeft(yScale).ticks(5));
    svg.select(".sl-grid").call(d3.axisLeft(yScale).ticks(5).tickSize(-(width - margin.left - margin.right)).tickFormat(""));

    // Draw lines
    for (let i = 0; i < loaded.length; i++) {
      const s = loaded[i];
      // Build array of {w, r} pairs for D3 line generator
      const points = s.wavelengths.map((w, j) => ({ w, r: s.reflectance[j] }));

      const lineGen = d3.line()
        .x(d => xScale(d.w))
        .y(d => yScale(d.r))
        .defined(d => d.w != null && d.r != null && isFinite(d.w) && isFinite(d.r));

      chartG.append("path")
        .datum(points)
        .attr("class", `sl-spectrum-line ${LINE_CLASSES[i % MAX_OVERLAY]}`)
        .attr("fill", "none")
        .attr("stroke-width", 1.5)
        .attr("d", lineGen);
    }
  }

  function onZoom(event) {
    const newX = event.transform.rescaleX(xScale);
    const newY = event.transform.rescaleY(yScale);

    svg.select(".sl-x-axis").call(d3.axisBottom(newX).ticks(10));
    svg.select(".sl-y-axis").call(d3.axisLeft(newY).ticks(5));

    chartG.selectAll("path.sl-spectrum-line")
      .attr("d", function () {
        const points = d3.select(this).datum();
        return d3.line()
          .x(d => newX(d.w))
          .y(d => newY(d.r))
          .defined(d => d.w != null && d.r != null && isFinite(d.w) && isFinite(d.r))(points);
      });
  }

  function resetZoom() {
    if (svg && zoom) svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);
    renderChart();
  }

  // ── Utilities ───────────────────────────────────────────────────

  function truncate(str, len) {
    return str.length > len ? str.slice(0, len) + "\u2026" : str;
  }

  function debounce(fn, ms) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
    };
  }

  function showEmpty(msg) {
    const tbody = document.getElementById("sl-results-body");
    if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="sl-empty">${msg}</td></tr>`;
  }

  return { init };
})();

// Initialize: try multiple strategies since load timing varies
if (typeof document$ !== "undefined") {
  // Zensical instant navigation
  document$.subscribe(() => {
    if (document.getElementById("sl-chart")) SL.init();
  });
} else if (document.readyState === "loading") {
  // Script loaded before DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("sl-chart")) SL.init();
  });
} else {
  // DOM already ready (script loaded at end of page)
  if (document.getElementById("sl-chart")) SL.init();
}
