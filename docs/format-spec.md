# speclib Format Specification v1.0

This document defines the interchange formats for speclib spectral archives.
Any compliant implementation (Python, Rust, R) MUST read and write data
conforming to this specification.

## 1. HDF5 Archive

The HDF5 archive is the source of truth. All other formats are derived from it.

### 1.1 File Structure

```
speclib_archive.h5
├── /metadata
│   ├── version           # scalar string: semver (e.g., "1.0.0")
│   ├── created           # scalar string: ISO 8601 timestamp
│   └── sources           # compound dataset: ingestion provenance
├── /{category}/
│   └── /{spectrum_id}/
│       ├── wavelengths   # float64 dataset, gzip-4, sorted ascending, µm
│       ├── reflectance   # float64 dataset, gzip-4, 0.0–1.0 scale
│       └── errors        # float64 dataset, gzip-4 (OPTIONAL)
└── ...
```

### 1.2 Category Groups

Top-level groups use the **lowercase enum value** of the material category:

| Group | MaterialCategory enum |
|-------|----------------------|
| `/mineral/` | MINERAL |
| `/rock/` | ROCK |
| `/soil/` | SOIL |
| `/vegetation/` | VEGETATION |
| `/vegetation_plot/` | VEGETATION_PLOT |
| `/water/` | WATER |
| `/manmade/` | MANMADE |
| `/mixture/` | MIXTURE |
| `/organic/` | ORGANIC |
| `/nonphotosynthetic_vegetation/` | NONPHOTOSYNTHETIC_VEGETATION |
| `/volatile/` | VOLATILE |
| `/ky_invasive/` | KY_INVASIVE |
| `/ky_mineral/` | KY_MINERAL |
| `/ky_reclamation/` | KY_RECLAMATION |

Groups are created on demand -- empty categories have no group.

### 1.3 Spectrum Datasets

Each spectrum is an HDF5 group at `/{category}/{spectrum_id}/` containing:

| Dataset | dtype | Compression | Required | Constraints |
|---------|-------|-------------|----------|-------------|
| `wavelengths` | float64 | gzip level 4 | YES | Sorted ascending, micrometers (um) |
| `reflectance` | float64 | gzip level 4 | YES | Nominally 0.0-1.0 (values outside range are flagged, not clipped) |
| `errors` | float64 | gzip level 4 | NO | Same length as wavelengths if present |

`wavelengths` and `reflectance` MUST have identical length.

### 1.4 Required Attributes

Every spectrum group MUST have these HDF5 attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Human-readable spectrum name |
| `spectrum_id` | string | Unique identifier: `{source}_{category}_{slug}_{hash8}` |
| `quality` | string | One of: VERIFIED, GOOD, FAIR, POOR, SUSPECT, DERIVED |
| `material_name` | string | Canonical material name |
| `material_category` | string | Enum value (see 1.2) |
| `source_library` | string | One of: USGS_SPLIB07, ECOSTRESS, ASTER_JPL, EMIT_L2B, KY_FIELD, CUSTOM |
| `source_record_id` | string | Original ID in upstream source |
| `measurement_type` | string | One of: LABORATORY, FIELD, AIRBORNE, SPACEBORNE, COMPUTED |
| `license` | string | Data license |
| `ingested_at` | string | ISO 8601 timestamp |
| `adapter_version` | string | Semver of the adapter that created this record |
| `source_filename` | string | Original filename from upstream source |

### 1.5 Optional Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `material_subcategory` | string | Subclass or finer classification |
| `formula` | string | Chemical formula or mineral class |
| `instrument` | string | Measurement instrument or method |
| `description` | string | Free-text description |
| `locality` | string | Collection locality |
| `citation` | string | Literature reference |
| `grain_size` | string | Grain size or particle size |
| `purity` | string | Sample purity assessment |
| `measurement_date` | string | ISO date of measurement |
| `geometry_wkt` | string | WKT geometry in EPSG:4326 (empty string if none) |
| `geometry_ky_wkt` | string | WKT geometry in EPSG:3089 (empty string if none) |
| `xrd_results` | string | XRD analysis results |
| `em_results` | string | Electron microscopy results |
| `extra` | string | JSON-encoded dict of additional key-value pairs |

Missing optional attributes SHOULD be stored as empty strings, not omitted.

### 1.6 Spectrum ID Generation

Deterministic: `{source}_{category}_{slug}_{hash8}`

- `source`: lowercase source_library value (e.g., `ecostress`)
- `category`: lowercase material_category value (e.g., `mineral`)
- `slug`: `name.lower().replace(" ", "_")[:40]`
- `hash8`: first 8 chars of `sha256(f"{source}:{category}:{name}:{source_filename}")`

### 1.7 Version Metadata

The `/metadata` group SHOULD contain:
- `version`: string, semver (current: `"1.0.0"`)
- `created`: string, ISO 8601 timestamp

Readers MUST check the major version and reject archives with incompatible versions.

## 2. Parquet Query Layer

Derived from HDF5. Regenerable. Uses snappy compression.

### 2.1 Catalog (`catalog.parquet`)

| Column | Arrow Type | Description |
|--------|-----------|-------------|
| `spectrum_id` | utf8 | Unique identifier |
| `name` | utf8 | Human-readable name |
| `material_category` | utf8 | Enum value |
| `source_library` | utf8 | Enum value |
| `quality` | utf8 | Quality flag enum value |
| `material_name` | utf8 | Canonical material name |
| `n_bands` | int64 | Number of spectral channels |
| `wavelength_min` | float64 | Minimum wavelength (um) |
| `wavelength_max` | float64 | Maximum wavelength (um) |
| `license` | utf8 | Data license |
| `citation` | utf8 | Literature reference |
| `instrument` | utf8 | Measurement instrument |
| `locality` | utf8 | Collection locality |

### 2.2 Spectra (`spectra/{category}.parquet`)

| Column | Arrow Type | Description |
|--------|-----------|-------------|
| `spectrum_id` | utf8 | Unique identifier |
| `name` | utf8 | Human-readable name |
| `wavelengths` | list\<float64\> | Wavelength array (um) |
| `reflectance` | list\<float64\> | Reflectance array (0.0-1.0) |

Category filename uses the lowercase enum value (e.g., `mineral.parquet`).

### 2.3 GeoParquet Extension

Spectra with spatial provenance include:
- `geometry`: WKB-encoded, EPSG:4326
- `geometry_ky`: WKB-encoded, EPSG:3089 (Kentucky data only)

## 3. JSON Catalog (Static Web)

### 3.1 Catalog Index (`catalog.json`)

Array of objects with the same fields as the Parquet catalog (2.1).

### 3.2 Individual Spectra (`spectra/{spectrum_id}.json`)

```json
{
  "spectrum_id": "ecostress_mineral_quartz_sio2_abc12345",
  "name": "Quartz SiO2",
  "wavelengths": [0.4, 0.41, "..."],
  "reflectance": [0.05, 0.051, "..."],
  "metadata": {
    "material_category": "MINERAL",
    "source_library": "ECOSTRESS",
    "quality": "GOOD",
    "material_name": "Quartz SiO2",
    "source_record_id": "S-2A",
    "measurement_type": "LABORATORY",
    "license": "CC0 / Public Domain",
    "description": "...",
    "locality": "...",
    "citation": "..."
  }
}
```

### 3.3 Taxonomy (`taxonomy.json`)

Nested tree of material categories:

```json
{
  "categories": [
    {"id": "MINERAL", "label": "Minerals", "children": []},
    {"id": "ROCK", "label": "Rocks", "children": []}
  ]
}
```

## 4. Enum Value Tables

### QualityFlag
VERIFIED, GOOD, FAIR, POOR, SUSPECT, DERIVED

### MaterialCategory
MINERAL, ROCK, SOIL, VEGETATION, VEGETATION_PLOT, WATER, MANMADE, MIXTURE, ORGANIC, NONPHOTOSYNTHETIC_VEGETATION, VOLATILE, KY_INVASIVE, KY_MINERAL, KY_RECLAMATION

### SourceLibrary
USGS_SPLIB07, ECOSTRESS, ASTER_JPL, EMIT_L2B, KY_FIELD, CUSTOM

### MeasurementType
LABORATORY, FIELD, AIRBORNE, SPACEBORNE, COMPUTED
