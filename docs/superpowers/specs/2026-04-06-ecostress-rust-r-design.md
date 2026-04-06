# Design Spec: ECOSTRESS Ingestion + Rust Crate + R Package

**Date:** 2026-04-06
**Status:** Approved
**Scope:** Three-phase expansion — ECOSTRESS data ingestion, Rust crate, R package

---

## 1. Format Contract

The interoperability layer across all three language packages is the **file format spec**, not shared compiled code. Each package (Python, Rust, R) implements read/write independently against this contract.

### HDF5 Archive Schema

- Group hierarchy (follows architecture.md conventions — plural for countable nouns, singular/collective otherwise): `/minerals/`, `/vegetation/`, `/soils/`, `/rocks/`, `/manmade/`, `/mixtures/`, `/nonphotosyntheticvegetation/`, `/ky/`
- Each spectrum dataset contains:
  - `wavelengths` — `float64[]`, micrometers (um), sorted ascending
  - `reflectance` — `float64[]`, 0.0-1.0 scale
  - `errors` — `float64[]`, measurement uncertainty (optional)
- Required HDF5 attributes per dataset:
  - `source_library` — string enum (USGS, ECOSTRESS, ASTER_JPL, EMIT, KY_FIELD)
  - `source_record_id` — original identifier from upstream source
  - `material_name` — human-readable name
  - `material_category` — string enum matching group hierarchy
  - `quality_flag` — string enum (GOOD, MARGINAL, POOR, UNVERIFIED)
  - `measurement_type` — string enum (LABORATORY, FIELD, AIRBORNE, SPACEBORNE)
  - `ingested_at` — ISO 8601 timestamp
  - `adapter_version` — semver string
- Optional attributes: `formula`, `description`, `locality`, `citation`, `license`, `instrument`, `collection_date`, `grain_size`, `genus`, `species`, `particle_size`, `chemistry`, `biophysical_properties`
- Compression: gzip level 4

### Parquet Query Schema

- `catalog.parquet` — metadata-only catalog for search/filter:
  - `spectrum_id` (string), `name` (string), `material_category` (string), `source_library` (string), `quality_flag` (string), `measurement_type` (string), `wavelength_min` (float64), `wavelength_max` (float64), `num_channels` (int32), `description` (string), `locality` (string), `citation` (string)
- `spectra/*.parquet` — per-category files with spectral arrays:
  - All catalog columns plus `wavelengths` (list<float64>), `reflectance` (list<float64>), `errors` (list<float64>, nullable)
- GeoParquet: `geometry` column in WKB, EPSG:4326. Kentucky data adds `geometry_ky` in EPSG:3089.
- Compression: snappy

### JSON Catalog Schema (Static Web)

- `catalog.json` — array of metadata objects matching Parquet catalog columns
- `spectra/{spectrum_id}.json` — individual spectrum with `wavelengths`, `reflectance`, `metadata` object
- `taxonomy.json` — nested material category tree

### Conformance Test Suite

- A `tests/conformance/` directory in the main repo containing:
  - Sample HDF5 archive with representative spectra from each category
  - Expected Parquet output
  - Expected JSON catalog output
  - Checksum manifests
- Any language implementation can run these to validate format compliance

### Naming Conventions

Consistent naming across all three packages and the format spec:

| Context | Convention | Examples |
|---------|-----------|----------|
| Type/class names | Singular PascalCase | `Spectrum`, `SpectralLibrary`, `QualityFlag` |
| Single item references | Singular | "a spectrum", `spectrum_id`, `loadSpectrum()` |
| Collection references | Plural | "3,311 spectra", `compareSpectra()` |
| HDF5 category groups | Plural for countable, singular for collective | `/minerals/`, `/rocks/`, `/soils/` but `/vegetation/`, `/manmade/`, `/nonphotosyntheticvegetation/` |
| Parquet/JSON directories | Plural | `spectra/*.parquet`, `spectra/{id}.json` |
| Enum values (Python) | Singular uppercase | `MINERAL`, `ROCK`, `VEGETATION` |
| Rust enum variants | Singular PascalCase | `Mineral`, `Rock`, `Vegetation` |
| R S4 classes | Singular PascalCase | `Spectrum`, `SpectralLibrary` |
| Source file names | Singular | `spectrum.rs`, `spectrum.R`, `spectrum.py` |
| Spectrum IDs | `{source}_{category}_{name_slug}_{hash8}` | `ecostress_mineral_quartz_a1b2c3d4` |

### Schema Versioning

- Archive version string stored in HDF5 `/metadata/version`
- Semver: breaking schema changes increment major version
- Readers must check version and reject incompatible archives with a clear error

---

## 2. Phase 1: ECOSTRESS Ingestion (Python)

### Data Source

ECOSTRESS Spectral Library download: 6,004 files (3,311 spectra + 2,692 ancillary + 1 manifest).

| Category | Spectrum Files |
|----------|---------------|
| mineral (silicate, carbonate, sulfate, oxide, etc.) | ~1,600 |
| vegetation (tree, shrub, grass) | ~1,000 |
| rock (igneous, sedimentary, metamorphic) | ~330 |
| nonphotosyntheticvegetation (bark, branches, etc.) | ~80 |
| soil (alfisol, aridisol, entisol, etc.) | ~60 |

### Adapter Fixes

#### 2.1 Header Parser Rewrite

Current `_read_header()` in `src/speclib/ingest/ecostress.py` treats lines positionally and stores raw lines (e.g., `"Name: Avena fatua"`) as values. The actual format is `Key: Value` pairs.

**Fix:** Parse each header line by splitting on the first colon. Key normalization: strip whitespace, convert to a canonical key set. Store only the value portion.

```python
# Before (broken):
header[_HEADER_FIELDS[i]] = line.strip()  # "Name: Avena fatua"

# After (correct):
key, _, value = line.partition(":")
header[key.strip()] = value.strip()       # "Avena fatua"
```

#### 2.2 Variable Header Fields

Header fields vary by material type:
- Minerals: `Name, Type, Class, Subclass, Particle Size, Sample No., Owner, ...`
- Vegetation: `Name, Type, Class, Genus, Species, Sample No., Owner, ...`

**Fix:** Remove the fixed `_HEADER_FIELDS` list. Parse key-value pairs dynamically. Normalize keys to a canonical mapping for downstream use:

```python
_KEY_NORMALIZE = {
    "sample no.": "sample_no",
    "wavelength range": "wavelength_range",
    "collection date": "collection_date",
    "x units": "wavelength_unit",
    "y units": "data_unit",
    "first x value": "first_x_value",
    "last x value": "last_x_value",
    "number of x values": "num_x_values",
    "additional information": "additional_info",
    "particle size": "particle_size",
}
```

#### 2.3 Descending Wavelength Sort

Some mineral spectra have wavelengths in descending order (e.g., 2.5 -> 0.4 um).

**Fix:** In `normalize()`, detect descending order and sort both wavelengths and reflectance arrays ascending:

```python
if len(wavelengths) > 1 and wavelengths[0] > wavelengths[-1]:
    sort_idx = np.argsort(wavelengths)
    wavelengths = wavelengths[sort_idx]
    reflectance = reflectance[sort_idx]
```

#### 2.4 Ancillary File Linking

2,692 `.ancillary.txt` files contain chemistry, biophysical properties, and literature references. The ancillary filename is typically referenced in the spectrum's `Additional Information` header field, and follows a parallel naming convention (`.ancillary.txt` vs `.spectrum.txt`).

**Fix:** During `fetch()` or `normalize()`, look for a paired ancillary file by replacing `.spectrum.txt` with `.ancillary.txt` in the path. Parse the ancillary file's key-value header and merge into `SampleMetadata`:
- `Chemistry` -> `metadata.chemistry`
- `Biophysical Properties` -> `metadata.biophysical_properties`
- `Reference` -> `metadata.citation` (append to existing citation if present)

#### 2.5 New Material Category

The ECOSTRESS data includes `nonphotosyntheticvegetation` as a material type, not currently in `MaterialCategory` enum or `_TYPE_MAP`.

**Fix:** Add `NONPHOTOSYNTHETIC_VEGETATION` to the `MaterialCategory` enum in `src/speclib/core/spectrum.py`. Add mapping in `_TYPE_MAP`:

```python
"nonphotosyntheticvegetation": "NONPHOTOSYNTHETIC_VEGETATION",
```

Add corresponding HDF5 group `/nonphotosyntheticvegetation/` to the archive schema.

#### 2.6 Data Start Detection

Current code assumes data starts after a fixed number of header lines. The actual data starts after the `Additional Information:` line followed by a blank line.

**Fix:** Detect data start by finding the blank line separator between header and data, rather than using a fixed line count.

### Ingestion Pipeline

1. Extract zip to `data/upstream/downloads/ecostress/`
2. Update `data/upstream/ecostress.yaml` with `data_dir` path
3. Run adapter: `discover()` -> `fetch()` -> `normalize()` -> `hdf5.write()`
4. Regenerate Parquet query layer from HDF5
5. Regenerate static JSON catalog

---

## 3. Phase 2: Rust Crate (`speclib-rs`)

### Target Users

- Geospatial pipeline developers using `gdal`, `geo`, `arrow-rs`
- Web developers needing client-side spectral operations via WASM
- Field/embedded users needing a fast standalone CLI

### Crate Structure

```
speclib-rs/
├── Cargo.toml                # Workspace root
├── speclib-core/             # Core types + I/O (library crate)
│   ├── src/
│   │   ├── lib.rs
│   │   ├── spectrum.rs       # Spectrum, Metadata, QualityFlag types
│   │   ├── library.rs        # SpectralLibrary collection + search/filter
│   │   ├── hdf5.rs           # HDF5 read/write (feature-gated: "hdf5")
│   │   ├── parquet.rs        # Parquet read/write via arrow-rs/parquet
│   │   ├── json.rs           # JSON catalog read/write (serde)
│   │   ├── resample.rs       # Gaussian SRF convolution, sensor profiles
│   │   ├── matching.rs       # Spectral angle mapper, least-squares matching
│   │   └── geo.rs            # GeoParquet support (feature-gated: "geo")
│   └── Cargo.toml
├── speclib-cli/              # CLI binary
│   ├── src/main.rs           # clap-based CLI
│   └── Cargo.toml
├── speclib-wasm/             # WASM target
│   ├── src/lib.rs            # wasm-bindgen API surface
│   └── Cargo.toml
└── tests/
    └── conformance/          # Format conformance tests
```

### Design Decisions

- **No ingestion adapters.** Ingestion is Python's domain (I/O-bound, messy upstream formats). Rust reads normalized HDF5/Parquet output.
- **Feature gates for heavy dependencies:**
  - `hdf5` — enables HDF5 read/write (requires system libhdf5)
  - `geo` — enables GeoParquet with `geo` crate types
  - `wasm` — enables wasm-bindgen target (mutually exclusive with `hdf5`)
  - Default features: Parquet + JSON + core types (no system deps)
- **Arrow-native internally.** Spectral arrays stored as Arrow `Float64Array`. Parquet I/O is zero-copy. Arrow IPC enables efficient WASM bridge to JavaScript.
- **`geo` crate integration.** GeoParquet reads produce `geo::Point` / `geo::Geometry`, interoperable with `proj`, `gdal`, `rstar` for spatial indexing.
- **Sensor response profiles bundled.** Landsat 8/9, Sentinel-2, AVIRIS, EMIT sensor response functions compiled into the crate as const data.

### CLI Commands

```
speclib search <query>          # Search catalog by name, category, source
speclib info <archive>          # Archive stats, spectrum count, categories
speclib export <id> --format    # Export spectrum (ASCII, JSON, CSV)
speclib resample <id> --sensor  # Resample to target sensor
speclib match <input> <archive> # Match input spectrum against library
speclib convert <in> <out>      # HDF5 <-> Parquet format conversion
```

### WASM API Surface

Narrow, focused on what the web viewer needs:

```typescript
// JS API (generated by wasm-bindgen)
loadSpectrum(json: string): Spectrum
resampleToSensor(spectrum: Spectrum, sensor: string): Spectrum
spectralAngle(a: Spectrum, b: Spectrum): number
compareSpectra(spectra: Spectrum[]): ComparisonResult
```

### Publishing

- `speclib-core` and `speclib-cli` to crates.io
- `@speclib/wasm` to npm
- GPL-3.0 license (matching Python package)

---

## 4. Phase 3: R Package (`speclib`)

### Target Users

- Academic researchers with field spectra in R (spectrolab, hsdar, prospectr)
- Remote sensing students doing spectral analysis exercises
- Operational analysts running spectral ID in R pipelines

### Package Structure

```
speclib-r/
├── DESCRIPTION                # GPL-3.0, Depends: R (>= 4.1)
├── NAMESPACE
├── R/
│   ├── spectrum.R             # S4 Spectrum and SpectralLibrary classes
│   ├── library.R              # read_speclib() — load from Parquet or JSON
│   ├── search.R               # search_speclib() — filter by material, wavelength, source
│   ├── resample.R             # resample_to_sensor() — Gaussian SRF convolution
│   ├── match.R                # spectral_angle(), spectral_match()
│   ├── plot.R                 # geom_spectrum(), autoplot.Spectrum()
│   └── convert.R              # as_hsdar(), as_spectrolab(), as_prospectr(), from_hsdar(), etc.
├── man/                       # roxygen2-generated documentation
│   └── figures/
│       └── logo.png           # Generated hex sticker
├── vignettes/
│   ├── getting-started.Rmd    # Load, browse, plot speclib data
│   ├── matching.Rmd           # Spectral identification workflow
│   └── integration.Rmd        # Interop with hsdar/spectrolab/prospectr
├── inst/
│   └── extdata/               # Small sample Parquet for examples and tests
├── data-raw/
│   └── hex-sticker.R          # Hex sticker generation script
└── tests/
    └── testthat/              # Format conformance + unit tests
```

### Design Decisions

- **Parquet-only I/O via `arrow` R package.** No HDF5 dependency — keeps installation simple, no system libhdf5 required. R users get the query layer.
- **S4 classes.** `Spectrum` and `SpectralLibrary` as formal S4 classes, idiomatic for the Bioconductor / spectral analysis community.
- **ggplot2 integration.** Custom `geom_spectrum()` geom and `autoplot()` methods. Accessible defaults: line styles + markers for distinguishing spectra, not color alone (WCAG compliance).
- **Interop converters.** Bidirectional conversion to/from `hsdar::Speclib`, `spectrolab::spectra`, `prospectr` objects so users integrate with existing workflows.
- **Resampling in native R.** Gaussian SRF convolution using R's stats/signal processing. Validated against the conformance test suite (same expected outputs as Python and Rust).
- **CRAN-publishable.** Only dependency requiring compilation is `arrow`. Vignettes work offline with bundled sample data in `inst/extdata/`.

### Hex Sticker

- Generated using the `hexSticker` R package in `data-raw/hex-sticker.R`
- Design: stylized vegetation reflectance curve showing the characteristic red-edge jump at ~0.7 um
- Dark background, spectral curve with gradient or color highlighting the red-edge feature
- Package name "speclib" along the bottom edge
- Output: PNG at `man/figures/logo.png`
- Used in README, pkgdown site, CRAN listing

---

## 5. Implementation Priority

| Order | Phase | Deliverable | Dependencies |
|-------|-------|-------------|-------------|
| 1 | Format contract | Schema spec + conformance tests | None |
| 2 | ECOSTRESS ingestion | Fixed adapter, 3,311 spectra ingested | Format contract |
| 3 | Rust crate | speclib-core + speclib-cli + speclib-wasm | Format contract |
| 4 | R package + hex sticker | speclib R package on CRAN | Format contract |

Phases 3 and 4 can proceed in parallel once the format contract is stable.

---

## 6. Out of Scope

- PyO3 bridge between Rust and Python (future optimization, not needed now)
- Ingestion adapters in Rust or R (Python owns ingestion)
- HDF5 write from R (R reads Parquet only)
- Mobile targets for Rust (future consideration)
