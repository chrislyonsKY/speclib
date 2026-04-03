# Spectral Library Browser

Search, compare, and download reflectance spectra from federated sources.

**2,592 spectra** across 8 categories: USGS splib07a minerals, vegetation, soils, artificial materials, organics, coatings, liquids, plus Kentucky invasive species field data (Lyons, Gyawali, Cristan, Acharya, Gebremedhin, & Andries, 2024).

<div class="sl-library">
  <div class="sl-controls">
    <div class="sl-search-bar">
      <input type="text" id="sl-search" placeholder="Search spectra (e.g., quartz, L.maackii, calcite...)" aria-label="Search spectra">
    </div>
    <div class="sl-filters">
      <select id="sl-filter-category" aria-label="Filter by category">
        <option value="">All Categories</option>
      </select>
      <select id="sl-filter-source" aria-label="Filter by source">
        <option value="">All Sources</option>
      </select>
      <select id="sl-filter-quality" aria-label="Filter by quality">
        <option value="">All Quality</option>
      </select>
      <select id="sl-view-mode" aria-label="Chart view mode">
        <option value="reflectance">Reflectance</option>
        <option value="continuum">Continuum Removed</option>
        <option value="derivative1">1st Derivative</option>
        <option value="derivative2">2nd Derivative</option>
      </select>
      <span id="sl-result-count" class="sl-count"></span>
    </div>
  </div>
  <div class="sl-main">
    <div class="sl-results-panel">
      <table id="sl-results-table" aria-label="Search results">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Source</th>
            <th>Bands</th>
            <th>Range (&#181;m)</th>
          </tr>
        </thead>
        <tbody id="sl-results-body">
          <tr><td colspan="5" class="sl-empty">Loading catalog...</td></tr>
        </tbody>
      </table>
    </div>
    <div class="sl-viewer-panel">
      <div class="sl-chart-container">
        <div id="sl-chart" role="img" aria-label="Spectral reflectance chart"></div>
        <div class="sl-chart-toolbar">
          <label><input type="checkbox" id="sl-toggle-landsat"> Landsat 8/9</label>
          <label><input type="checkbox" id="sl-toggle-sentinel"> Sentinel-2</label>
          <label><input type="checkbox" id="sl-toggle-absorptions"> Absorptions</label>
          <label><input type="checkbox" id="sl-toggle-convolve"> Convolve</label>
          <button id="sl-btn-stats" title="Show mean +/- std envelope">Stats</button>
          <button id="sl-btn-indices" title="Compute NDVI, NDWI, etc.">Indices</button>
          <button id="sl-btn-reset-zoom" title="Reset zoom">Reset</button>
          <button id="sl-btn-clear" title="Clear all spectra">Clear</button>
          <button id="sl-btn-csv" title="Download as CSV">CSV</button>
          <button id="sl-btn-png" title="Download as PNG">PNG</button>
          <span id="sl-crosshair-readout" class="sl-readout"></span>
        </div>
        <div id="sl-indices-panel" style="display:none"></div>
      </div>
      <div class="sl-metadata-panel" id="sl-metadata">
        <h3>Spectrum Details</h3>
        <p class="sl-hint">Click a spectrum in the table to view it.</p>
        <p class="sl-hint">Compare up to 6 spectra with distinct line styles (WCAG-compliant).</p>
        <p class="sl-hint">See <a href="methodology/">Methodology</a> for processing details.</p>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script src="../js/spectral-viewer.js"></script>
