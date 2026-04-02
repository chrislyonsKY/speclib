# Spectral Data Model

## Core Concepts

### Spectrum

The fundamental unit in speclib. Every spectrum contains:

| Field | Type | Description |
|-------|------|-------------|
| `wavelengths` | `ndarray[float64]` | Wavelength positions in micrometers (µm), sorted ascending |
| `reflectance` | `ndarray[float64]` | Reflectance values, scaled 0.0–1.0 |
| `errors` | `ndarray[float64]` | Measurement uncertainty per band (optional) |
| `metadata` | `SampleMetadata` | Provenance, material properties, analytical context |
| `quality` | `QualityFlag` | USGS-convention purity/quality indicator |

### Conventions

- **Wavelength units**: Always micrometers (µm). Adapters convert from nm or cm⁻¹ on ingestion.
- **Reflectance scale**: Always 0.0–1.0. Adapters convert from percentage (0–100) on ingestion.
- **Spectral gaps**: Stored as `NaN` in arrays, documented in metadata.
- **No implicit resampling**: Data is stored exactly as measured. Resampling is an explicit operation.

### Quality Flags

Following USGS conventions:

| Flag | Meaning |
|------|---------|
| `REFERENCE` | Reference standard, highest confidence |
| `HIGH` | High purity, well-characterized sample |
| `MEDIUM` | Moderate confidence, may have mixtures |
| `LOW` | Low confidence, use with caution |
| `UNVALIDATED` | Not yet validated against reference |

## Storage Model

### HDF5 Archive (Source of Truth)

Spectra are organized hierarchically by material category:

```
speclib_archive.h5
├── /metadata          # Archive-level provenance
├── /minerals          # USGS mineral spectra
├── /vegetation        # Plant spectra including KY invasives
├── /soils             # Soil spectra
├── /manmade           # Artificial materials
├── /mixtures          # Mixed spectra
└── /ky                # Kentucky-specific collections
    ├── /invasives
    ├── /minerals
    └── /reclamation
```

### Parquet Query Layer (Derived)

Flat, columnar format optimized for search and filtering. Regenerated from HDF5 on demand. GeoParquet extension for spatially-referenced spectra.

## Provenance

Every spectrum tracks its origin:

- `source_library` — which upstream library (USGS, ECOSTRESS, ASTER, EMIT, KY)
- `source_record_id` — original ID in the upstream library
- `ingested_at` — when the spectrum was added to speclib
- `adapter_version` — version of the ingestion adapter used
