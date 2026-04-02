# Architecture — speclib

## System Overview

speclib is a three-layer federated spectral signature library:

```
┌─────────────────────────────────────────────────────────────┐
│                    Distribution Layer                         │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │  GitHub Pages     │    │  FastAPI Server (optional)    │   │
│  │  Static D3.js     │    │  Jinja + D3.js + REST API    │   │
│  │  viewer           │    │  Parquet query backend        │   │
│  └────────┬─────────┘    └──────────────┬───────────────┘   │
│           │                              │                    │
│     Static JSON                    Parquet files              │
│           │                              │                    │
├───────────┼──────────────────────────────┼────────────────────┤
│           │        Storage Layer         │                    │
│  ┌────────┴──────────────────────────────┴───────────────┐   │
│  │                  Build Pipeline                        │   │
│  │         HDF5 archive → Parquet query layer             │   │
│  │         Parquet → Static JSON catalog                  │   │
│  └────────┬──────────────────────────────────────────────┘   │
│           │                                                   │
│  ┌────────┴──────────────────────────────────────────────┐   │
│  │              HDF5 Archive (source of truth)            │   │
│  │   /minerals/  /vegetation/  /soils/  /manmade/  /ky/  │   │
│  └────────┬──────────────────────────────────────────────┘   │
│           │                                                   │
├───────────┼───────────────────────────────────────────────────┤
│           │        Ingestion Layer                            │
│  ┌────────┴──────────────────────────────────────────────┐   │
│  │              Adapter Registry                          │   │
│  │  ┌──────┐ ┌──────────┐ ┌───────┐ ┌──────┐           │   │
│  │  │ USGS │ │ECOSTRESS │ │ ASTER │ │ EMIT │  + custom  │   │
│  │  └──────┘ └──────────┘ └───────┘ └──────┘           │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Layer Details

### 1. Ingestion Layer

Each upstream spectral library gets a dedicated adapter inheriting from `BaseAdapter`:

```python
class BaseAdapter(ABC):
    """Base class for all spectral library ingestion adapters."""

    @abstractmethod
    def discover(self) -> list[SourceRecord]:
        """List available spectra from the upstream source."""

    @abstractmethod
    def fetch(self, record_id: str) -> RawSpectrum:
        """Retrieve a single raw spectrum with metadata."""

    @abstractmethod
    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert source-native format to speclib's internal Spectrum model."""
```

Adapter responsibilities:
- **USGSAdapter** — Parses splib07a ASCII files and SPECPR binary. Maps USGS chapter codes (ChXX) to speclib material categories. Preserves original SPECPR record numbers.
- **ECOSTRESSAdapter** — Reads ECOSTRESS spectral library CSV/HDF5 files. Maps ECOSTRESS categories to speclib taxonomy.
- **ASTERAdapter** — Reads ASTER/JPL spectral library files. Handles the JPL-specific header format.
- **EMITAdapter** — Reads EMIT L2B mineral identification NetCDF4 granules. Extracts per-pixel mineral spectra with geolocation.

### 2. Storage Layer

**HDF5 Archive** (source of truth):
```
speclib_archive.h5
├── /metadata
│   ├── version          # Archive version string
│   ├── created          # ISO 8601 timestamp
│   └── sources[]        # Provenance records for each ingested source
├── /minerals
│   ├── /quartz_HS32.4B
│   │   ├── wavelengths  # float64 array (µm)
│   │   ├── reflectance  # float64 array (0.0–1.0)
│   │   ├── errors       # float64 array (measurement uncertainty)
│   │   └── .attrs       # metadata dict (source, purity, grain_size, ...)
│   └── ...
├── /vegetation
│   ├── /lonicera_maackii_leaf_2020    # Amur honeysuckle (Lyons et al. 2024)
│   └── ...
├── /soils
├── /manmade
├── /mixtures
└── /ky                                 # Kentucky-specific chapter
    ├── /invasives
    ├── /minerals
    └── /reclamation
```

**Parquet Query Layer** (derived, regenerable):
```
query/
├── catalog.parquet          # Full searchable catalog (metadata only, no arrays)
├── spectra/
│   ├── minerals.parquet     # Wavelength + reflectance arrays as list columns
│   ├── vegetation.parquet
│   └── ...
└── ky/
    └── invasives.parquet
```

GeoParquet extension: Spectra with spatial provenance (EMIT pixels, field collection sites) include a `geometry` column in WGS84 (EPSG:4326) for interoperability, plus `geometry_ky` in EPSG:3089 for Kentucky-specific data.

### 3. Distribution Layer

**Static Viewer (GitHub Pages)**:
```
web/static/
├── index.html              # Entry point — search + browse
├── viewer.html             # Spectral plot viewer (D3.js)
├── js/
│   ├── app.js              # Search, filter, catalog navigation
│   ├── spectral-chart.js   # D3.js spectral plotting engine
│   └── compare.js          # Multi-spectra overlay comparison
├── css/
│   └── style.css           # Clean, USGS-inspired data-first design
└── data/                   # Pre-built by build pipeline
    ├── catalog.json        # Searchable metadata index
    ├── spectra/            # Individual spectrum JSON files
    │   ├── quartz_HS32.json
    │   └── ...
    └── taxonomy.json       # Material category tree
```

**FastAPI Server (optional)**:
```python
# Endpoints
GET  /api/v1/spectra                    # Search/filter catalog
GET  /api/v1/spectra/{spectrum_id}      # Single spectrum with full data
GET  /api/v1/spectra/{spectrum_id}/plot  # Server-rendered plot (PNG/SVG)
GET  /api/v1/compare                    # Multi-spectra comparison
GET  /api/v1/export/{spectrum_id}       # Export in requested format
GET  /api/v1/resample/{spectrum_id}     # Resample to target sensor
POST /api/v1/match                      # Spectral matching/identification
GET  /api/v1/taxonomy                   # Material category tree
```

Server templates use Jinja2 for HTML pages, embedding D3.js charts client-side.

## Data Flow

### Ingestion Pipeline
```
upstream source → adapter.discover() → adapter.fetch() → adapter.normalize()
    → quality_check() → storage.hdf5.write() → HDF5 archive
```

### Build Pipeline (static site generation)
```
HDF5 archive → storage.parquet.export() → Parquet query files
    → build/generate_static.py → JSON catalog + spectrum files
    → web/static/data/
```

### Query Flow (FastAPI)
```
HTTP request → route handler → Parquet reader → filter/search
    → serialize response (JSON, or render Jinja template with D3.js)
```

## Spectral Resampling Engine

A critical capability: convolving library spectra to match target sensor characteristics.

Supported resampling targets (v1):
- Landsat 8/9 OLI/TIRS
- Sentinel-2 MSI
- AVIRIS-Classic (multiple years)
- AVIRIS-NG
- EMIT
- ASD FieldSpec (full range)
- HyMap
- Hyperion
- Custom (user-defined wavelength/bandpass pairs)

Approach: Gaussian spectral response functions convolved with oversampled (cubic-spline interpolated) library spectra, following the splib07b methodology.

## Module Interfaces

### Core Models
- `Spectrum` — wavelengths, reflectance, errors, metadata, quality flags
- `SpectralLibrary` — collection of Spectrum objects with search/filter
- `SampleMetadata` — provenance, material properties, analytical results
- `SensorResponse` — wavelength/bandpass pairs for resampling targets
- `QualityFlag` — enumeration following USGS purity/quality conventions

### Key Interfaces
- `BaseAdapter` — ABC for all ingestion adapters
- `BaseExporter` — ABC for all export format writers
- `StorageBackend` — Protocol for HDF5 and Parquet backends

## Technology Decisions

See `ai-dev/decisions/` for full ADRs. Summary:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Archival format | HDF5 | Hierarchical, self-describing, scientific standard, handles large arrays |
| Query format | Parquet | Columnar, fast filtering, GeoParquet for spatial, earthForge-compatible |
| Web viz | D3.js | Full control over spectral chart rendering, no framework overhead |
| Web framework | FastAPI + Jinja | Lightweight, async, good for data APIs |
| Static hosting | GitHub Pages | Zero cost, USGS-like distribution ethos |
| CLI | Click | Standard Python CLI framework |
| SPECPR compat | Custom binary R/W | Required for round-trip fidelity with USGS tools |
