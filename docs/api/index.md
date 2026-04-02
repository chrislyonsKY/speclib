# API Reference

## Core Models

### `speclib.core.Spectrum`

The fundamental spectral data container.

| Attribute | Type | Description |
|-----------|------|-------------|
| `wavelengths` | `ndarray[float64]` | Wavelength positions in µm |
| `reflectance` | `ndarray[float64]` | Reflectance values (0.0–1.0) |
| `errors` | `ndarray[float64]` | Measurement uncertainty |
| `metadata` | `SampleMetadata` | Provenance and material properties |
| `quality` | `QualityFlag` | USGS-convention quality indicator |

**Methods:**

- `plot()` — render spectrum with matplotlib
- `export(path, format)` — export to target format
- `resample(sensor)` — convolve to target sensor response

### `speclib.core.SpectralLibrary`

Collection of spectra with search and filtering.

**Methods:**

- `from_hdf5(path)` — load from HDF5 archive
- `search(query, category=None)` — text search across metadata
- `filter(**kwargs)` — filter by metadata attributes

### `speclib.core.SampleMetadata`

Provenance and analytical context for a spectrum.

### `speclib.core.QualityFlag`

Enumeration: `REFERENCE`, `HIGH`, `MEDIUM`, `LOW`, `UNVALIDATED`

## REST API (FastAPI)

When running the optional server (`speclib serve`), the following endpoints are available:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/spectra` | Search and filter catalog |
| `GET` | `/api/v1/spectra/{id}` | Single spectrum with full data |
| `GET` | `/api/v1/spectra/{id}/plot` | Server-rendered plot (PNG/SVG) |
| `GET` | `/api/v1/compare` | Multi-spectra comparison |
| `GET` | `/api/v1/export/{id}` | Export in requested format |
| `GET` | `/api/v1/resample/{id}` | Resample to target sensor |
| `POST` | `/api/v1/match` | Spectral matching/identification |
| `GET` | `/api/v1/taxonomy` | Material category tree |
