/**
 * speclib — Plotly.js spectral chart engine
 *
 * Interactive spectral plot with zoom, pan, crosshair readout,
 * multi-spectra overlay, sensor band overlays, absorption annotations,
 * continuum removal, spectral derivatives, band math, and convolution preview.
 */

const SpectralChart = (() => {
    'use strict';

    // --- Trace palette: colorblind-safe, WCAG 3:1 contrast ---
    const PALETTE = [
        ['#005ea2', 'solid',     'circle'],
        ['#d54309', 'dash',      'square'],
        ['#00a91c', 'dot',       'diamond'],
        ['#112e51', 'dashdot',   'triangle-up'],
        ['#7ca8d2', 'longdash',  'cross'],
        ['#e5a000', 'longdashdot','x'],
    ];

    // --- Sensor band definitions (center wavelength, FWHM in µm) ---
    const SENSOR_BANDS = {
        landsat: {
            name: 'Landsat 8/9 OLI',
            bands: [
                { label: 'Coastal', center: 0.443, width: 0.016, color: 'rgba(100,100,255,0.12)' },
                { label: 'Blue',    center: 0.482, width: 0.060, color: 'rgba(0,0,220,0.10)' },
                { label: 'Green',   center: 0.561, width: 0.057, color: 'rgba(0,180,0,0.10)' },
                { label: 'Red',     center: 0.655, width: 0.037, color: 'rgba(220,0,0,0.10)' },
                { label: 'NIR',     center: 0.865, width: 0.028, color: 'rgba(150,0,0,0.10)' },
                { label: 'SWIR1',   center: 1.609, width: 0.085, color: 'rgba(180,120,0,0.10)' },
                { label: 'SWIR2',   center: 2.201, width: 0.187, color: 'rgba(120,80,0,0.10)' },
            ]
        },
        sentinel: {
            name: 'Sentinel-2 MSI',
            bands: [
                { label: 'B1',  center: 0.443, width: 0.020, color: 'rgba(100,100,255,0.12)' },
                { label: 'B2',  center: 0.490, width: 0.065, color: 'rgba(0,0,220,0.10)' },
                { label: 'B3',  center: 0.560, width: 0.035, color: 'rgba(0,180,0,0.10)' },
                { label: 'B4',  center: 0.665, width: 0.030, color: 'rgba(220,0,0,0.10)' },
                { label: 'B5',  center: 0.705, width: 0.015, color: 'rgba(200,50,0,0.10)' },
                { label: 'B6',  center: 0.740, width: 0.015, color: 'rgba(180,70,0,0.10)' },
                { label: 'B7',  center: 0.783, width: 0.020, color: 'rgba(160,90,0,0.10)' },
                { label: 'B8',  center: 0.842, width: 0.115, color: 'rgba(140,0,0,0.10)' },
                { label: 'B8A', center: 0.865, width: 0.020, color: 'rgba(130,0,0,0.10)' },
                { label: 'B11', center: 1.610, width: 0.090, color: 'rgba(180,120,0,0.10)' },
                { label: 'B12', center: 2.190, width: 0.180, color: 'rgba(120,80,0,0.10)' },
            ]
        }
    };

    // --- Diagnostic absorption features ---
    const ABSORPTION_FEATURES = [
        { wl: 0.43,  label: 'Fe\u00B3\u207A',  color: '#dc2626' },
        { wl: 0.55,  label: 'Fe\u00B2\u207A',  color: '#16a34a' },
        { wl: 0.67,  label: 'Chlorophyll',      color: '#059669' },
        { wl: 0.87,  label: 'Fe\u00B2\u207A/Fe\u00B3\u207A', color: '#b45309' },
        { wl: 1.0,   label: 'Fe\u00B2\u207A',  color: '#b45309' },
        { wl: 1.4,   label: 'H\u2082O/OH',      color: '#0891b2' },
        { wl: 1.9,   label: 'H\u2082O',         color: '#0891b2' },
        { wl: 2.2,   label: 'Al-OH',            color: '#7c3aed' },
        { wl: 2.31,  label: 'Mg-OH/CO\u2083',   color: '#6d28d9' },
        { wl: 2.35,  label: 'CO\u2083\u00B2\u207B', color: '#4f46e5' },
    ];

    // --- Band math indices ---
    const BAND_INDICES = {
        NDVI:  { name: 'NDVI',  formula: '(NIR - Red) / (NIR + Red)', nir: 0.865, red: 0.655 },
        NDWI:  { name: 'NDWI',  formula: '(Green - NIR) / (Green + NIR)', green: 0.56, nir: 0.865 },
        NDSI:  { name: 'NDSI',  formula: '(Green - SWIR1) / (Green + SWIR1)', green: 0.56, swir1: 1.61 },
        EVI:   { name: 'EVI',   formula: '2.5*(NIR-Red)/(NIR+6*Red-7.5*Blue+1)', nir: 0.865, red: 0.655, blue: 0.48 },
    };

    // --- State ---
    let traces = [];
    let rawTraceData = [];  // Store original {wl, refl} for transforms
    let chartInitialized = false;
    let showLandsat = false;
    let showSentinel = false;
    let showAbsorptions = false;
    let viewMode = 'reflectance'; // 'reflectance', 'continuum', 'derivative1', 'derivative2'
    let showConvolution = false;

    const chartEl = document.getElementById('spectral-chart');

    // ========== SPECTRAL TRANSFORMS ==========

    /** Compute convex hull upper envelope for continuum removal */
    function computeContinuum(wl, refl) {
        const n = wl.length;
        if (n < 3) return refl.slice();

        // Build upper convex hull
        const hull = [0];
        for (let i = 1; i < n; i++) {
            while (hull.length >= 2) {
                const a = hull[hull.length - 2];
                const b = hull[hull.length - 1];
                const cross = (wl[b] - wl[a]) * (refl[i] - refl[a]) - (refl[b] - refl[a]) * (wl[i] - wl[a]);
                if (cross >= 0) hull.pop();
                else break;
            }
            hull.push(i);
        }

        // Interpolate continuum line
        const continuum = new Float64Array(n);
        let hi = 0;
        for (let i = 0; i < n; i++) {
            while (hi < hull.length - 1 && wl[i] > wl[hull[hi + 1]]) hi++;
            const a = hull[hi];
            const b = hull[Math.min(hi + 1, hull.length - 1)];
            if (a === b) {
                continuum[i] = refl[a];
            } else {
                const t = (wl[i] - wl[a]) / (wl[b] - wl[a]);
                continuum[i] = refl[a] + t * (refl[b] - refl[a]);
            }
        }

        // Continuum-removed = reflectance / continuum
        const removed = new Float64Array(n);
        for (let i = 0; i < n; i++) {
            removed[i] = continuum[i] > 0.001 ? refl[i] / continuum[i] : 1.0;
        }
        return Array.from(removed);
    }

    /** Compute spectral derivative (1st or 2nd order) */
    function computeDerivative(wl, refl, order) {
        const n = wl.length;
        if (n < 3) return { dwl: wl.slice(), drefl: refl.slice() };

        // 1st derivative: dR/dλ
        let dwl = [];
        let drefl = [];
        for (let i = 1; i < n - 1; i++) {
            const dw = wl[i + 1] - wl[i - 1];
            if (dw > 0) {
                dwl.push(wl[i]);
                drefl.push((refl[i + 1] - refl[i - 1]) / dw);
            }
        }

        if (order === 2 && dwl.length > 2) {
            // 2nd derivative from 1st
            const dwl2 = [];
            const drefl2 = [];
            for (let i = 1; i < dwl.length - 1; i++) {
                const dw = dwl[i + 1] - dwl[i - 1];
                if (dw > 0) {
                    dwl2.push(dwl[i]);
                    drefl2.push((drefl[i + 1] - drefl[i - 1]) / dw);
                }
            }
            return { dwl: dwl2, drefl: drefl2 };
        }

        return { dwl, drefl };
    }

    /** Interpolate reflectance at a target wavelength */
    function interpAt(wl, refl, target) {
        for (let i = 0; i < wl.length - 1; i++) {
            if (wl[i] <= target && wl[i + 1] >= target) {
                const t = (target - wl[i]) / (wl[i + 1] - wl[i]);
                return refl[i] + t * (refl[i + 1] - refl[i]);
            }
        }
        return null;
    }

    /** Convolve spectrum to sensor bands using Gaussian response */
    function convolveToBands(wl, refl, sensorKey) {
        const sensor = SENSOR_BANDS[sensorKey];
        if (!sensor) return [];
        const results = [];
        for (const band of sensor.bands) {
            const sigma = band.width / 2.355; // FWHM to sigma
            let sumW = 0, sumWR = 0;
            for (let i = 0; i < wl.length; i++) {
                const d = wl[i] - band.center;
                const w = Math.exp(-0.5 * (d / sigma) ** 2);
                sumW += w;
                sumWR += w * refl[i];
            }
            if (sumW > 0) {
                results.push({ label: band.label, center: band.center, value: sumWR / sumW });
            }
        }
        return results;
    }

    /** Compute band index value */
    function computeIndex(wl, refl, indexKey) {
        const idx = BAND_INDICES[indexKey];
        if (!idx) return null;

        if (indexKey === 'NDVI') {
            const nir = interpAt(wl, refl, idx.nir);
            const red = interpAt(wl, refl, idx.red);
            if (nir !== null && red !== null && (nir + red) !== 0) return (nir - red) / (nir + red);
        } else if (indexKey === 'NDWI') {
            const green = interpAt(wl, refl, idx.green);
            const nir = interpAt(wl, refl, idx.nir);
            if (green !== null && nir !== null && (green + nir) !== 0) return (green - nir) / (green + nir);
        } else if (indexKey === 'NDSI') {
            const green = interpAt(wl, refl, idx.green);
            const swir1 = interpAt(wl, refl, idx.swir1);
            if (green !== null && swir1 !== null && (green + swir1) !== 0) return (green - swir1) / (green + swir1);
        } else if (indexKey === 'EVI') {
            const nir = interpAt(wl, refl, idx.nir);
            const red = interpAt(wl, refl, idx.red);
            const blue = interpAt(wl, refl, idx.blue);
            if (nir !== null && red !== null && blue !== null) {
                const denom = nir + 6 * red - 7.5 * blue + 1;
                if (denom !== 0) return 2.5 * (nir - red) / denom;
            }
        }
        return null;
    }

    // ========== LAYOUT ==========

    function getYAxisLabel() {
        switch (viewMode) {
            case 'continuum': return 'Continuum-Removed Reflectance';
            case 'derivative1': return 'dR/d\u03BB (1st Derivative)';
            case 'derivative2': return 'd\u00B2R/d\u03BB\u00B2 (2nd Derivative)';
            default: return 'Reflectance';
        }
    }

    function getYAxisRange() {
        switch (viewMode) {
            case 'continuum': return [0.0, 1.1];
            case 'derivative1': return undefined; // auto
            case 'derivative2': return undefined;
            default: return [-0.02, 1.05];
        }
    }

    function getLayout() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const gridColor = isDark ? '#2a3042' : '#e5e7eb';
        const textColor = isDark ? '#9aa3b5' : '#5a6577';
        const bgColor = isDark ? '#1a1f2e' : '#ffffff';
        const paperBg = isDark ? '#1a1f2e' : '#ffffff';

        const shapes = [];
        const annotations = [];

        // Sensor band shapes (only in reflectance mode)
        if (viewMode === 'reflectance' || viewMode === 'continuum') {
            if (showLandsat) {
                for (const band of SENSOR_BANDS.landsat.bands) {
                    shapes.push({
                        type: 'rect', xref: 'x', yref: 'paper',
                        x0: band.center - band.width / 2, x1: band.center + band.width / 2,
                        y0: 0, y1: 1, fillcolor: band.color, line: { width: 0 }, layer: 'below',
                    });
                    annotations.push({
                        x: band.center, y: 1.02, xref: 'x', yref: 'paper',
                        text: band.label, showarrow: false, font: { size: 9, color: textColor },
                    });
                }
            }
            if (showSentinel) {
                for (const band of SENSOR_BANDS.sentinel.bands) {
                    shapes.push({
                        type: 'rect', xref: 'x', yref: 'paper',
                        x0: band.center - band.width / 2, x1: band.center + band.width / 2,
                        y0: 0, y1: 1,
                        fillcolor: band.color.replace('0.10', '0.08').replace('0.12', '0.10'),
                        line: { width: 1, color: band.color.replace('0.10', '0.25').replace('0.12', '0.30'), dash: 'dot' },
                        layer: 'below',
                    });
                }
            }
        }

        if (showAbsorptions) {
            for (const feat of ABSORPTION_FEATURES) {
                shapes.push({
                    type: 'line', xref: 'x', yref: 'paper',
                    x0: feat.wl, x1: feat.wl, y0: 0, y1: 0.92,
                    line: { color: feat.color, width: 1, dash: 'dot' }, layer: 'below',
                });
                annotations.push({
                    x: feat.wl, y: 0.95, xref: 'x', yref: 'paper',
                    text: feat.label, showarrow: false,
                    font: { size: 8, color: feat.color }, textangle: -45,
                });
            }
        }

        const yRange = getYAxisRange();
        return {
            xaxis: {
                title: { text: 'Wavelength (\u00B5m)', font: { size: 12 }, standoff: 8 },
                gridcolor: gridColor, zerolinecolor: gridColor,
                tickfont: { size: 11, color: textColor },
                tickformat: '.2f', hoverformat: '.4f', fixedrange: false,
            },
            yaxis: {
                title: { text: getYAxisLabel(), font: { size: 12 }, standoff: 8 },
                gridcolor: gridColor, zerolinecolor: gridColor,
                tickfont: { size: 11, color: textColor },
                tickformat: '.4f', hoverformat: '.4f',
                range: yRange, fixedrange: false,
            },
            plot_bgcolor: bgColor, paper_bgcolor: paperBg,
            font: { family: '"Public Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color: textColor },
            margin: { l: 65, r: 20, t: 10, b: 50 },
            hovermode: 'x unified', dragmode: 'zoom', showlegend: false,
            shapes, annotations,
        };
    }

    function getConfig() {
        return {
            responsive: true, displaylogo: false,
            modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d'],
            toImageButtonOptions: { format: 'png', filename: 'speclib_chart', width: 1600, height: 800, scale: 2 },
        };
    }

    // ========== RENDERING ==========

    /** Rebuild all traces from rawTraceData applying current viewMode */
    function rebuildTraces() {
        if (!chartInitialized) return;
        const plotData = [];

        for (let i = 0; i < rawTraceData.length; i++) {
            const { wl, refl } = rawTraceData[i];
            const [color, dash] = PALETTE[i];
            let x, y;

            switch (viewMode) {
                case 'continuum':
                    x = wl;
                    y = computeContinuum(wl, refl);
                    break;
                case 'derivative1': {
                    const d = computeDerivative(wl, refl, 1);
                    x = d.dwl; y = d.drefl;
                    break;
                }
                case 'derivative2': {
                    const d = computeDerivative(wl, refl, 2);
                    x = d.dwl; y = d.drefl;
                    break;
                }
                default:
                    x = wl; y = refl;
            }

            plotData.push({
                x, y, type: 'scattergl', mode: 'lines',
                name: traces[i].name,
                line: { color, width: 1.5, dash },
                hovertemplate: `<b>${traces[i].name}</b><br>%{x:.4f} \u00B5m<br>${getYAxisLabel()}: %{y:.4f}<extra></extra>`,
            });

            // Add convolution preview points
            if (showConvolution && viewMode === 'reflectance') {
                for (const sensorKey of ['landsat', 'sentinel']) {
                    const show = sensorKey === 'landsat' ? showLandsat : showSentinel;
                    if (!show) continue;
                    const conv = convolveToBands(wl, refl, sensorKey);
                    plotData.push({
                        x: conv.map(c => c.center),
                        y: conv.map(c => c.value),
                        type: 'scatter', mode: 'markers',
                        name: `${traces[i].name} (${SENSOR_BANDS[sensorKey].name})`,
                        marker: { color, size: 10, symbol: PALETTE[i][2], line: { width: 1.5, color: '#fff' } },
                        hovertemplate: `<b>%{text}</b><br>%{x:.3f} \u00B5m<br>Convolved: %{y:.4f}<extra></extra>`,
                        text: conv.map(c => c.label),
                        showlegend: false,
                    });
                }
            }
        }

        Plotly.react(chartEl, plotData, getLayout(), getConfig());
    }

    // ========== PUBLIC API ==========

    function init() {
        if (chartInitialized) return;
        Plotly.newPlot(chartEl, [], getLayout(), getConfig());
        chartInitialized = true;
    }

    function addTrace(spectrumData) {
        if (!chartInitialized) init();
        if (traces.length >= 6) return false;
        if (traces.find(t => t.id === spectrumData.id)) return false;

        const idx = traces.length;
        const [color, dash, symbol] = PALETTE[idx];

        // Filter out nulls and store raw data
        const wl = [], refl = [];
        for (let i = 0; i < spectrumData.wavelengths.length; i++) {
            if (spectrumData.reflectance[i] !== null && spectrumData.reflectance[i] !== undefined) {
                wl.push(spectrumData.wavelengths[i]);
                refl.push(spectrumData.reflectance[i]);
            }
        }

        rawTraceData.push({ wl, refl });
        traces.push({ id: spectrumData.id, name: spectrumData.name, color, dash });

        rebuildTraces();
        updateButtons();
        return true;
    }

    function removeTrace(spectrumId) {
        const idx = traces.findIndex(t => t.id === spectrumId);
        if (idx < 0) return;

        traces.splice(idx, 1);
        rawTraceData.splice(idx, 1);

        // Reassign palette
        traces.forEach((t, i) => {
            const [color, dash] = PALETTE[i];
            t.color = color;
            t.dash = dash;
        });

        rebuildTraces();
        updateButtons();
    }

    function clearAll() {
        if (!chartInitialized) return;
        traces = [];
        rawTraceData = [];
        viewMode = 'reflectance';
        showConvolution = false;
        Plotly.purge(chartEl);
        chartInitialized = false;
        init();
        updateButtons();
    }

    function getTraces() { return traces.map(t => ({ ...t })); }
    function hasTrace(spectrumId) { return traces.some(t => t.id === spectrumId); }

    function setOverlays({ landsat, sentinel, absorptions } = {}) {
        if (landsat !== undefined) showLandsat = landsat;
        if (sentinel !== undefined) showSentinel = sentinel;
        if (absorptions !== undefined) showAbsorptions = absorptions;
        rebuildTraces();
    }

    function setViewMode(mode) {
        if (['reflectance', 'continuum', 'derivative1', 'derivative2'].includes(mode)) {
            viewMode = mode;
            rebuildTraces();
        }
    }

    function setConvolution(enabled) {
        showConvolution = enabled;
        rebuildTraces();
    }

    function refreshTheme() { rebuildTraces(); }

    /** Compute band indices for all loaded traces */
    function getBandIndices() {
        const results = [];
        for (let i = 0; i < rawTraceData.length; i++) {
            const { wl, refl } = rawTraceData[i];
            const entry = { name: traces[i].name, color: traces[i].color };
            for (const key of Object.keys(BAND_INDICES)) {
                entry[key] = computeIndex(wl, refl, key);
            }
            results.push(entry);
        }
        return results;
    }

    /** Compute mean + stddev envelope from all loaded traces (resampled to common grid) */
    function computeGroupStats() {
        if (rawTraceData.length < 2) return null;

        // Find common wavelength range
        let minWl = -Infinity, maxWl = Infinity;
        for (const { wl } of rawTraceData) {
            minWl = Math.max(minWl, wl[0]);
            maxWl = Math.min(maxWl, wl[wl.length - 1]);
        }
        if (minWl >= maxWl) return null;

        // Create common grid (use first trace's density)
        const ref = rawTraceData[0].wl;
        const grid = ref.filter(w => w >= minWl && w <= maxWl);
        if (grid.length < 10) return null;

        // Interpolate all traces to grid
        const allRefl = rawTraceData.map(({ wl, refl }) =>
            grid.map(gw => interpAt(wl, refl, gw) || 0)
        );

        // Compute mean and std
        const mean = grid.map((_, j) => {
            let sum = 0;
            for (const r of allRefl) sum += r[j];
            return sum / allRefl.length;
        });
        const std = grid.map((_, j) => {
            let sumSq = 0;
            for (const r of allRefl) sumSq += (r[j] - mean[j]) ** 2;
            return Math.sqrt(sumSq / allRefl.length);
        });

        return { wl: grid, mean, std, upper: mean.map((m, i) => m + std[i]), lower: mean.map((m, i) => m - std[i]) };
    }

    /** Add group stats envelope as traces */
    function showGroupStats() {
        const stats = computeGroupStats();
        if (!stats) return;

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const fillColor = isDark ? 'rgba(91,141,239,0.15)' : 'rgba(26,86,219,0.12)';
        const meanColor = isDark ? '#5b8def' : '#1a56db';

        // Add envelope and mean as additional Plotly traces
        const newTraces = [
            {
                x: [...stats.wl, ...stats.wl.slice().reverse()],
                y: [...stats.upper, ...stats.lower.slice().reverse()],
                fill: 'toself', fillcolor: fillColor,
                line: { color: 'transparent' }, type: 'scatter', mode: 'lines',
                name: '\u00B1 1\u03C3 Envelope', hoverinfo: 'skip', showlegend: false,
            },
            {
                x: stats.wl, y: stats.mean, type: 'scatter', mode: 'lines',
                name: `Mean (n=${rawTraceData.length})`,
                line: { color: meanColor, width: 2.5 },
                hovertemplate: `<b>Mean</b><br>%{x:.4f} \u00B5m<br>Reflectance: %{y:.4f}<extra></extra>`,
            },
        ];

        Plotly.addTraces(chartEl, newTraces);
    }

    function downloadCSV() {
        if (traces.length === 0) return;
        const { wl, refl } = rawTraceData[0];
        let csv = 'wavelength_um';
        for (const t of traces) csv += `,${t.name.replace(/,/g, ';')}`;
        csv += '\n';
        for (let i = 0; i < wl.length; i++) {
            csv += wl[i];
            for (let j = 0; j < rawTraceData.length; j++) {
                const r = rawTraceData[j];
                csv += `,${r.refl[i] !== undefined ? r.refl[i] : ''}`;
            }
            csv += '\n';
        }
        const blob = new Blob([csv], { type: 'text/csv' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `speclib_export_${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
    }

    function downloadPNG() {
        if (!chartInitialized) return;
        Plotly.downloadImage(chartEl, { format: 'png', filename: `speclib_chart_${Date.now()}`, width: 1600, height: 800, scale: 2 });
    }

    function updateButtons() {
        const csvBtn = document.getElementById('btn-download-csv');
        const pngBtn = document.getElementById('btn-download-png');
        if (csvBtn) csvBtn.disabled = traces.length === 0;
        if (pngBtn) pngBtn.disabled = traces.length === 0;
    }

    return {
        init, addTrace, removeTrace, clearAll, getTraces, hasTrace,
        setOverlays, setViewMode, setConvolution, refreshTheme,
        downloadCSV, downloadPNG, getBandIndices, computeGroupStats, showGroupStats,
        PALETTE, BAND_INDICES,
    };
})();
