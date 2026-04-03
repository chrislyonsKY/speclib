/**
 * speclib — Main application
 *
 * Catalog loading, search, filtering, table, comparison mode, and URL state.
 */

(() => {
    'use strict';

    // --- State ---
    let catalog = [];
    let taxonomy = {};
    let filtered = [];
    let activeCategory = null;
    let activeInstruments = new Set();
    let activeMeasurements = new Set();
    let searchQuery = '';
    let sortKey = 'name';
    let sortDir = 'asc';
    let page = 0;
    const PAGE_SIZE = 50;
    let selectedId = null;

    // Category display labels
    const CATEGORY_LABELS = {
        ky_invasive: 'KY Invasive Species',
        minerals: 'Minerals',
        vegetation: 'Vegetation',
        soils_mixtures: 'Soils & Mixtures',
        artificial: 'Artificial Materials',
        coatings: 'Coatings',
        liquids: 'Liquids',
        organics: 'Organic Compounds',
    };

    const CATEGORY_ICONS = {
        ky_invasive: '&#127807;',
        minerals: '&#9830;',
        vegetation: '&#9752;',
        soils_mixtures: '&#9683;',
        artificial: '&#9635;',
        coatings: '&#9641;',
        liquids: '&#9832;',
        organics: '&#9883;',
    };

    // --- DOM refs ---
    const searchInput = document.getElementById('search-input');
    const searchCount = document.getElementById('search-count');
    const categoryNav = document.getElementById('category-nav');
    const instrumentFilters = document.getElementById('instrument-filters');
    const measurementFilters = document.getElementById('measurement-filters');
    const sidebarStats = document.getElementById('sidebar-stats');
    const resultsBody = document.getElementById('results-body');
    const resultsCount = document.getElementById('results-count');
    const chartTitle = document.getElementById('chart-title');
    const metadataPanel = document.getElementById('metadata-panel');
    const comparisonTray = document.getElementById('comparison-tray');
    const trayItems = document.getElementById('tray-items');
    const trayCount = document.getElementById('tray-count');
    const chartLegend = document.getElementById('chart-legend');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const pageInfo = document.getElementById('page-info');

    // --- Init ---
    async function init() {
        try {
            const [catRes, taxRes] = await Promise.all([
                fetch('data/catalog.json'),
                fetch('data/taxonomy.json'),
            ]);
            const catData = await catRes.json();
            catalog = catData.spectra;
            taxonomy = (await taxRes.json()).categories;
        } catch (err) {
            console.error('Failed to load catalog:', err);
            resultsBody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--c-danger)">Failed to load catalog data. Ensure data/catalog.json exists.</td></tr>';
            return;
        }

        buildSidebar();
        buildInstrumentFilters();
        buildMeasurementFilters();
        bindEvents();
        SpectralChart.init();
        applyFilters();
        restoreFromURL();
    }

    // --- Sidebar ---
    function buildSidebar() {
        // "All" item
        let html = `<div class="cat-item active" data-cat="all">
            <span>${'All Spectra'}</span>
            <span class="cat-count">${catalog.length}</span>
        </div>`;

        const catOrder = ['ky_invasive', 'minerals', 'vegetation', 'soils_mixtures', 'artificial', 'organics', 'coatings', 'liquids'];
        for (const cat of catOrder) {
            const info = taxonomy[cat];
            if (!info) continue;
            html += `<div class="cat-item" data-cat="${cat}">
                <span>${CATEGORY_ICONS[cat] || ''} ${CATEGORY_LABELS[cat] || cat}</span>
                <span class="cat-count">${info.count}</span>
            </div>`;
        }
        categoryNav.innerHTML = html;

        // Stats
        sidebarStats.innerHTML = `
            <div style="padding:0 0.5rem">${catalog.length.toLocaleString()} spectra</div>
            <div style="padding:0 0.5rem">${Object.keys(taxonomy).length} categories</div>
            <div style="padding:0 0.5rem">Source: USGS splib07a</div>
        `;
    }

    function buildInstrumentFilters() {
        const instruments = [...new Set(catalog.map(s => s.instrument))].sort();
        instrumentFilters.innerHTML = instruments.map(inst =>
            `<label><input type="checkbox" value="${inst}" checked> ${inst}</label>`
        ).join('');
        activeInstruments = new Set(instruments);
    }

    function buildMeasurementFilters() {
        const measurements = [...new Set(catalog.map(s => s.measurement))].sort();
        measurementFilters.innerHTML = measurements.map(m =>
            `<label><input type="checkbox" value="${m}" checked> ${m}</label>`
        ).join('');
        activeMeasurements = new Set(measurements);
    }

    // --- Events ---
    function bindEvents() {
        // Search
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchQuery = searchInput.value.trim().toLowerCase();
                page = 0;
                applyFilters();
            }, 150);
        });

        // Keyboard shortcut: / to focus search
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement !== searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
            if (e.key === 'Escape' && document.activeElement === searchInput) {
                searchInput.blur();
            }
        });

        // Category nav
        categoryNav.addEventListener('click', (e) => {
            const item = e.target.closest('.cat-item');
            if (!item) return;
            const cat = item.dataset.cat;
            activeCategory = cat === 'all' ? null : cat;
            categoryNav.querySelectorAll('.cat-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
            page = 0;
            applyFilters();
        });

        // Instrument filters
        instrumentFilters.addEventListener('change', () => {
            activeInstruments = new Set(
                [...instrumentFilters.querySelectorAll('input:checked')].map(cb => cb.value)
            );
            page = 0;
            applyFilters();
        });

        // Measurement filters
        measurementFilters.addEventListener('change', () => {
            activeMeasurements = new Set(
                [...measurementFilters.querySelectorAll('input:checked')].map(cb => cb.value)
            );
            page = 0;
            applyFilters();
        });

        // Table sorting
        document.querySelectorAll('#results-table th.sortable').forEach(th => {
            th.addEventListener('click', () => {
                const key = th.dataset.sort;
                if (sortKey === key) {
                    sortDir = sortDir === 'asc' ? 'desc' : 'asc';
                } else {
                    sortKey = key;
                    sortDir = 'asc';
                }
                renderTable();
            });
        });

        // Pagination
        btnPrev.addEventListener('click', () => { if (page > 0) { page--; renderTable(); } });
        btnNext.addEventListener('click', () => {
            if ((page + 1) * PAGE_SIZE < filtered.length) { page++; renderTable(); }
        });

        // View mode
        document.getElementById('view-mode').addEventListener('change', (e) => {
            SpectralChart.setViewMode(e.target.value);
        });

        // Chart overlays
        document.getElementById('toggle-landsat').addEventListener('change', (e) => {
            SpectralChart.setOverlays({ landsat: e.target.checked });
        });
        document.getElementById('toggle-sentinel').addEventListener('change', (e) => {
            SpectralChart.setOverlays({ sentinel: e.target.checked });
        });
        document.getElementById('toggle-absorptions').addEventListener('change', (e) => {
            SpectralChart.setOverlays({ absorptions: e.target.checked });
        });
        document.getElementById('toggle-convolution').addEventListener('change', (e) => {
            SpectralChart.setConvolution(e.target.checked);
        });

        // Group stats
        document.getElementById('btn-stats').addEventListener('click', () => {
            SpectralChart.showGroupStats();
        });

        // Band math
        document.getElementById('btn-band-math').addEventListener('click', () => {
            const panel = document.getElementById('band-math-panel');
            const indices = SpectralChart.getBandIndices();
            if (indices.length === 0) { panel.classList.add('hidden'); return; }

            let html = '';
            for (const entry of indices) {
                html += `<span class="index-result"><span class="index-swatch" style="background:${entry.color}"></span>`;
                html += `<span class="index-label">${escapeHTML(entry.name)}</span>`;
                for (const key of Object.keys(SpectralChart.BAND_INDICES)) {
                    const val = entry[key];
                    const formatted = val !== null ? val.toFixed(3) : 'N/A';
                    html += ` <span class="index-label">${key}:</span><span class="index-value">${formatted}</span>`;
                }
                html += '</span>';
            }
            panel.innerHTML = html;
            panel.classList.remove('hidden');
            panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });

        // Clear chart
        document.getElementById('btn-clear-chart').addEventListener('click', () => {
            SpectralChart.clearAll();
            document.getElementById('view-mode').value = 'reflectance';
            document.getElementById('band-math-panel').classList.add('hidden');
            selectedId = null;
            metadataPanel.classList.add('hidden');
            chartTitle.textContent = 'Select a spectrum to view';
            comparisonTray.classList.remove('active');
            trayItems.innerHTML = '';
            chartLegend.innerHTML = '';
            updateTrayCount();
            updateCompareButtons();
            updateURL();
        });

        // Downloads
        document.getElementById('btn-download-csv').addEventListener('click', () => SpectralChart.downloadCSV());
        document.getElementById('btn-download-png').addEventListener('click', () => SpectralChart.downloadPNG());

        // Clear tray
        document.getElementById('btn-clear-tray').addEventListener('click', () => {
            SpectralChart.clearAll();
            selectedId = null;
            comparisonTray.classList.remove('active');
            trayItems.innerHTML = '';
            chartLegend.innerHTML = '';
            chartTitle.textContent = 'Select a spectrum to view';
            metadataPanel.classList.add('hidden');
            updateTrayCount();
            updateCompareButtons();
            updateURL();
        });

        // Theme toggle
        document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

        // Restore theme preference
        const savedTheme = localStorage.getItem('speclib-theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    }

    // --- Theme ---
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('speclib-theme', next);
        SpectralChart.refreshTheme();
    }

    // --- Filtering ---
    function applyFilters() {
        filtered = catalog.filter(s => {
            if (activeCategory && s.category !== activeCategory) return false;
            if (!activeInstruments.has(s.instrument)) return false;
            if (!activeMeasurements.has(s.measurement)) return false;
            if (searchQuery) {
                const haystack = `${s.name} ${s.category} ${s.instrument}`.toLowerCase();
                const terms = searchQuery.split(/\s+/);
                if (!terms.every(t => haystack.includes(t))) return false;
            }
            return true;
        });
        renderTable();
        searchCount.textContent = `${filtered.length.toLocaleString()} results`;
        resultsCount.textContent = `${filtered.length.toLocaleString()} of ${catalog.length.toLocaleString()}`;
    }

    // --- Table rendering ---
    function renderTable() {
        // Sort
        const sorted = [...filtered].sort((a, b) => {
            let va = a[sortKey], vb = b[sortKey];
            if (typeof va === 'string') va = va.toLowerCase();
            if (typeof vb === 'string') vb = vb.toLowerCase();
            if (va < vb) return sortDir === 'asc' ? -1 : 1;
            if (va > vb) return sortDir === 'asc' ? 1 : -1;
            return 0;
        });

        // Update sort indicators
        document.querySelectorAll('#results-table th.sortable').forEach(th => {
            th.classList.remove('sorted-asc', 'sorted-desc');
            if (th.dataset.sort === sortKey) {
                th.classList.add(sortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
            }
        });

        // Paginate
        const start = page * PAGE_SIZE;
        const pageData = sorted.slice(start, start + PAGE_SIZE);
        const totalPages = Math.ceil(sorted.length / PAGE_SIZE) || 1;

        resultsBody.innerHTML = pageData.map(s => {
            const isCompared = SpectralChart.hasTrace(s.id);
            const isSelected = s.id === selectedId;
            return `<tr data-id="${s.id}" class="${isSelected ? 'selected' : ''}" tabindex="0" role="row">
                <td class="col-compare">
                    <button class="compare-btn ${isCompared ? 'active' : ''}" data-id="${s.id}"
                            aria-label="${isCompared ? 'Remove from comparison' : 'Add to comparison'}"
                            title="${isCompared ? 'Remove from comparison' : 'Add to comparison'}">&#10003;</button>
                </td>
                <td class="col-name" title="${s.name}">${highlightMatch(s.name)}</td>
                <td class="col-category"><span class="category-badge cat-${s.category}">${CATEGORY_LABELS[s.category] || s.category}</span></td>
                <td class="col-instrument">${s.instrument}</td>
                <td class="col-range">${s.wl_min}–${s.wl_max}</td>
                <td class="col-bands" style="text-align:right">${s.n_bands.toLocaleString()}</td>
            </tr>`;
        }).join('');

        // Pagination
        btnPrev.disabled = page === 0;
        btnNext.disabled = (page + 1) * PAGE_SIZE >= sorted.length;
        pageInfo.textContent = `Page ${page + 1} of ${totalPages}`;

        // Row click → load spectrum
        resultsBody.querySelectorAll('tr').forEach(tr => {
            tr.addEventListener('click', (e) => {
                if (e.target.closest('.compare-btn')) return;
                loadSpectrum(tr.dataset.id);
            });
            tr.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    loadSpectrum(tr.dataset.id);
                }
            });
        });

        // Compare button clicks
        resultsBody.querySelectorAll('.compare-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleCompare(btn.dataset.id);
            });
        });
    }

    function highlightMatch(text) {
        if (!searchQuery) return escapeHTML(text);
        const terms = searchQuery.split(/\s+/).filter(Boolean);
        let result = escapeHTML(text);
        for (const term of terms) {
            const regex = new RegExp(`(${escapeRegex(term)})`, 'gi');
            result = result.replace(regex, '<mark>$1</mark>');
        }
        return result;
    }

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // --- Spectrum loading ---
    async function loadSpectrum(id) {
        selectedId = id;

        // Update table selection styling
        resultsBody.querySelectorAll('tr').forEach(tr => {
            tr.classList.toggle('selected', tr.dataset.id === id);
        });

        try {
            const res = await fetch(`data/spectra/${id}.json`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            // If not already in comparison, add as primary trace
            if (!SpectralChart.hasTrace(id)) {
                // If this is the first trace (just viewing, not comparing), clear previous
                const currentTraces = SpectralChart.getTraces();
                if (currentTraces.length === 1 && !document.querySelector('.compare-btn.active')) {
                    SpectralChart.clearAll();
                }
                SpectralChart.addTrace(data);
            }

            // Update chart title
            chartTitle.textContent = data.name;

            // Show metadata
            showMetadata(id, data);
            updateLegend();
            updateTray();
            updateURL();
        } catch (err) {
            console.error('Failed to load spectrum:', err);
            chartTitle.textContent = 'Error loading spectrum';
        }
    }

    // --- Comparison ---
    async function toggleCompare(id) {
        if (SpectralChart.hasTrace(id)) {
            SpectralChart.removeTrace(id);
        } else {
            if (SpectralChart.getTraces().length >= 6) return;
            try {
                const res = await fetch(`data/spectra/${id}.json`);
                const data = await res.json();
                SpectralChart.addTrace(data);
            } catch (err) {
                console.error('Failed to load spectrum for comparison:', err);
                return;
            }
        }

        updateCompareButtons();
        updateLegend();
        updateTray();
        updateURL();
    }

    function updateCompareButtons() {
        resultsBody.querySelectorAll('.compare-btn').forEach(btn => {
            const isActive = SpectralChart.hasTrace(btn.dataset.id);
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-label', isActive ? 'Remove from comparison' : 'Add to comparison');
        });
    }

    function updateLegend() {
        const traces = SpectralChart.getTraces();
        if (traces.length === 0) {
            chartLegend.innerHTML = '';
            return;
        }
        chartLegend.innerHTML = traces.map(t =>
            `<span class="legend-item" data-id="${t.id}">
                <span class="legend-swatch" style="background:${t.color}"></span>
                ${escapeHTML(t.name)}
                <span class="legend-remove" data-id="${t.id}" title="Remove">&times;</span>
            </span>`
        ).join('');

        chartLegend.querySelectorAll('.legend-remove').forEach(el => {
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleCompare(el.dataset.id);
            });
        });
    }

    function updateTray() {
        const traces = SpectralChart.getTraces();
        updateTrayCount();

        if (traces.length <= 1) {
            comparisonTray.classList.remove('active');
            return;
        }

        comparisonTray.classList.add('active');
        trayItems.innerHTML = traces.map(t =>
            `<span class="tray-chip">
                <span class="tray-chip-color" style="background:${t.color}"></span>
                ${escapeHTML(t.name)}
                <span class="tray-chip-remove" data-id="${t.id}" title="Remove">&times;</span>
            </span>`
        ).join('');

        trayItems.querySelectorAll('.tray-chip-remove').forEach(el => {
            el.addEventListener('click', () => toggleCompare(el.dataset.id));
        });
    }

    function updateTrayCount() {
        const count = SpectralChart.getTraces().length;
        trayCount.textContent = `(${count}/6)`;
    }

    // --- Metadata panel ---
    function showMetadata(id, data) {
        const entry = catalog.find(s => s.id === id);
        if (!entry) return;

        metadataPanel.classList.remove('hidden');
        document.getElementById('meta-title').textContent = data.name;

        const fields = [
            ['Category', CATEGORY_LABELS[entry.category] || entry.category],
            ['Source', entry.source],
            ['Instrument', entry.instrument],
            ['Range', `${entry.instrument_range}`],
            ['Measurement', entry.measurement],
            ['Bands', entry.n_bands.toLocaleString()],
            ['λ range', `${entry.wl_min} – ${entry.wl_max} µm`],
            ['Reflectance', `${entry.refl_min} – ${entry.refl_max}`],
            ['Quality', entry.quality],
            ['License', entry.license],
        ];
        if (entry.record_id) {
            fields.push(['USGS Record', `#${entry.record_id}`]);
        }

        document.getElementById('meta-fields').innerHTML = fields.map(([k, v]) =>
            `<dt>${k}</dt><dd>${v}</dd>`
        ).join('');

        document.getElementById('meta-citation').textContent = entry.citation || '';
    }

    // --- URL state (permalink) ---
    function updateURL() {
        const traces = SpectralChart.getTraces();
        const ids = traces.map(t => t.id);
        const params = new URLSearchParams();
        if (ids.length > 0) params.set('s', ids.join(','));
        if (activeCategory) params.set('cat', activeCategory);
        if (searchQuery) params.set('q', searchQuery);
        const hash = params.toString();
        history.replaceState(null, '', hash ? `#${hash}` : window.location.pathname);
    }

    async function restoreFromURL() {
        const hash = window.location.hash.slice(1);
        if (!hash) return;

        const params = new URLSearchParams(hash);

        // Restore category
        const cat = params.get('cat');
        if (cat && taxonomy[cat]) {
            activeCategory = cat;
            categoryNav.querySelectorAll('.cat-item').forEach(el => {
                el.classList.toggle('active', el.dataset.cat === cat);
            });
            applyFilters();
        }

        // Restore search
        const q = params.get('q');
        if (q) {
            searchInput.value = q;
            searchQuery = q.toLowerCase();
            applyFilters();
        }

        // Restore spectra
        const spectraStr = params.get('s');
        if (spectraStr) {
            const ids = spectraStr.split(',').slice(0, 6);
            for (const id of ids) {
                try {
                    const res = await fetch(`data/spectra/${id}.json`);
                    if (!res.ok) continue;
                    const data = await res.json();
                    SpectralChart.addTrace(data);
                } catch { /* skip invalid */ }
            }
            if (ids.length > 0) {
                selectedId = ids[0];
                chartTitle.textContent = SpectralChart.getTraces()[0]?.name || 'Spectrum';
                // Load metadata for first spectrum
                const first = catalog.find(s => s.id === ids[0]);
                if (first) {
                    try {
                        const res = await fetch(`data/spectra/${ids[0]}.json`);
                        const data = await res.json();
                        showMetadata(ids[0], data);
                    } catch { /* skip */ }
                }
            }
            updateLegend();
            updateTray();
            updateCompareButtons();
        }
    }

    // --- Boot ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
