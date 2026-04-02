# Specification — speclib v0.1.0

## Project Summary

speclib is a federated spectral signature library platform that aggregates spectra from major public repositories (USGS splib07, ECOSTRESS, ASTER/JPL, EMIT L2B) into a unified, searchable collection with a Kentucky-focused chapter. It provides a Python package for researchers and a web interface for discovery.

## Scope

### In Scope (v0.1.0)

1. **Core data model** — Spectrum, SpectralLibrary, SampleMetadata, QualityFlag classes
2. **Ingestion adapters** — USGS splib07 (ASCII + SPECPR), ECOSTRESS, ASTER/JPL, EMIT L2B
3. **Dual storage** — HDF5 archival backend, Parquet query layer with build pipeline
4. **Export formats** — .esl (Esri), .sli (ENVI), SPECPR binary, ASCII columnar, JSON
5. **Spectral resampling** — Convolution engine with sensor response function library
6. **CLI** — Command-line interface for ingest, export, search, resample, build
7. **Static web viewer** — GitHub Pages site with D3.js spectral browser
8. **Optional FastAPI server** — Self-hosted API with Jinja templates
9. **Kentucky chapter** — Seed with Lyons et al. 2024 invasive species spectral data
10. **PyPI distribution** — Installable via `pip install speclib`

### Out of Scope (v0.1.0)

- User-contributed spectra upload workflow
- Authentication / access control on the API
- Real-time spectral matching against uploaded imagery
- Mobile-responsive web interface (desktop-first)
- Automated CI/CD for upstream library syncing
- ArcGIS Pro add-in integration

## Functional Requirements

### FR-1: Core Data Model

- **FR-1.1** — `Spectrum` stores wavelength array (µm), reflectance array (0.0–1.0), optional error array, quality flags, and metadata reference
- **FR-1.2** — `SampleMetadata` stores material name, category, subcategory, provenance (source library, record ID), measurement conditions (instrument, date, grain size, purity), analytical results (XRD, EM, XRF where available), and optional geometry (WGS84)
- **FR-1.3** — `QualityFlag` enum: VERIFIED, GOOD, FAIR, POOR, SUSPECT, following USGS purity conventions
- **FR-1.4** — `SpectralLibrary` provides search by name, category, wavelength range, source, quality; filter by material type; iterate over spectra

### FR-2: Ingestion

- **FR-2.1** — USGS adapter reads splib07a ASCII files preserving original record IDs, chapter assignments, and all metadata fields
- **FR-2.2** — USGS adapter reads SPECPR binary format for native round-trip capability
- **FR-2.3** — ECOSTRESS adapter reads the ECOSTRESS spectral library (CSV format with header metadata)
- **FR-2.4** — ASTER adapter reads JPL ASTER spectral library files
- **FR-2.5** — EMIT adapter reads L2B mineral identification NetCDF4 granules, extracting per-pixel identified mineral spectra with geolocation
- **FR-2.6** — All adapters produce normalized `Spectrum` objects with full provenance tracking
- **FR-2.7** — Ingestion is idempotent — re-running an adapter updates existing records, does not duplicate
- **FR-2.8** — Adapter registry allows discovery of available adapters and their status

### FR-3: Storage

- **FR-3.1** — HDF5 archive organizes spectra hierarchically by material category with per-spectrum attributes
- **FR-3.2** — HDF5 archive is the single source of truth; all other formats are derived
- **FR-3.3** — Parquet query layer is generated from HDF5 via build pipeline
- **FR-3.4** — Parquet catalog contains searchable metadata without spectral arrays (lightweight index)
- **FR-3.5** — Parquet spectra files contain wavelength + reflectance as list columns, partitioned by category
- **FR-3.6** — GeoParquet extension adds geometry column for spatially-referenced spectra (EMIT, field collections)
- **FR-3.7** — Kentucky spatial data uses EPSG:3089; all other spatial data uses EPSG:4326

### FR-4: Export

- **FR-4.1** — .esl export produces valid Esri Spectral Library files readable by ArcGIS Pro Spectral Library Browser
- **FR-4.2** — .sli export produces valid ENVI spectral library files with companion .hdr
- **FR-4.3** — SPECPR export produces binary files compatible with USGS SPECPR/PRISM software
- **FR-4.4** — ASCII export follows USGS splib07a column format (wavelength, reflectance, errors per line)
- **FR-4.5** — JSON export produces self-describing documents with metadata + spectral arrays
- **FR-4.6** — All exports support single spectrum or batch (full library / filtered subset)

### FR-5: Resampling

- **FR-5.1** — Spectral convolution engine resamples library spectra to target sensor response functions
- **FR-5.2** — Built-in sensor profiles: Landsat 8/9 OLI, Sentinel-2 MSI, AVIRIS-Classic, AVIRIS-NG, EMIT, ASD FieldSpec, HyMap, Hyperion
- **FR-5.3** — Custom sensor support via user-defined wavelength/bandpass CSV
- **FR-5.4** — Resampling uses cubic-spline oversampling followed by Gaussian convolution (splib07b method)
- **FR-5.5** — Output includes resampled reflectance + effective wavelengths for the target sensor

### FR-6: CLI

- **FR-6.1** — `speclib ingest <source> [--config path]` — Run an ingestion adapter
- **FR-6.2** — `speclib search <query> [--category] [--source] [--quality]` — Search the library
- **FR-6.3** — `speclib export <spectrum_id> --format <fmt> [--output path]` — Export spectra
- **FR-6.4** — `speclib resample <spectrum_id> --sensor <name> [--output path]` — Resample to sensor
- **FR-6.5** — `speclib build` — Generate Parquet query layer + static JSON from HDF5 archive
- **FR-6.6** — `speclib info <spectrum_id>` — Display metadata for a spectrum
- **FR-6.7** — `speclib stats` — Summary statistics (counts by category, source, quality)

### FR-7: Web Viewer (Static)

- **FR-7.1** — Searchable catalog with text search and category filters
- **FR-7.2** — Interactive D3.js spectral plot with zoom, pan, crosshair readout
- **FR-7.3** — Multi-spectra overlay comparison (up to 6 simultaneous spectra)
- **FR-7.4** — Sensor band overlay (show Landsat/Sentinel/etc. bands on spectral plot)
- **FR-7.5** — Download individual spectra in JSON or ASCII format
- **FR-7.6** — Material category tree navigation
- **FR-7.7** — Metadata panel showing provenance, quality, measurement conditions
- **FR-7.8** — Permalink URLs for individual spectra

### FR-8: FastAPI Server (Optional)

- **FR-8.1** — REST API endpoints per architecture.md specification
- **FR-8.2** — Jinja-templated HTML pages with embedded D3.js charts
- **FR-8.3** — OpenAPI/Swagger documentation auto-generated
- **FR-8.4** — Reads from Parquet query layer (not HDF5 directly)
- **FR-8.5** — CORS enabled for cross-origin API access

### FR-9: Kentucky Chapter

- **FR-9.1** — Category structure: /ky/invasives/, /ky/minerals/, /ky/reclamation/
- **FR-9.2** — Seed with Lyons et al. 2024 Amur honeysuckle (Lonicera maackii) and Callery pear (Pyrus calleryana) leaf-level spectral data
- **FR-9.3** — All KY spatial data in EPSG:3089 (Kentucky Single Zone, NAD83)
- **FR-9.4** — KY spectra carry citation metadata linking to Lyons et al. 2024

## Non-Functional Requirements

- **NFR-1** — Library search returns results in <100ms for catalogs up to 50,000 spectra
- **NFR-2** — Static viewer loads initial catalog in <3 seconds on broadband
- **NFR-3** — HDF5 archive supports incremental updates without full rebuild
- **NFR-4** — Parquet query layer rebuild completes in <5 minutes for full library
- **NFR-5** — All Python code passes ruff linting with default rules
- **NFR-6** — Test coverage ≥80% for core, ingest, export, and storage modules
- **NFR-7** — SPECPR binary export round-trips with USGS reference files (bit-level header compat)

## Acceptance Criteria (v0.1.0 Release Gate)

1. Successfully ingest USGS splib07a mineral chapter (>500 spectra) into HDF5
2. Successfully ingest at least one additional source (ECOSTRESS or ASTER)
3. Export a spectrum to all 5 formats and verify readability in target tools
4. Resample a mineral spectrum to Landsat 8 OLI bands, compare with USGS s07_L8 reference
5. Build pipeline generates valid static JSON catalog from HDF5 archive
6. Static viewer renders spectral plots, search works, multi-spectra comparison works
7. CLI commands complete without errors for ingest, search, export, resample, build
8. KY invasive species seed data present and browsable
9. `pip install speclib` succeeds in a clean virtualenv
10. README documents installation, quickstart, and basic usage
