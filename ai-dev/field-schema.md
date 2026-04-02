# Field Schema — speclib

## Core Models

### Spectrum

The fundamental data unit. A single spectral measurement with metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `spectrum_id` | str | Yes | Unique identifier (format: `{source}_{category}_{name}_{hash8}`) |
| `name` | str | Yes | Human-readable name (e.g., "Quartz GDS32 med-coarse grain") |
| `wavelengths` | ndarray[float64] | Yes | Wavelength positions in micrometers (µm) |
| `reflectance` | ndarray[float64] | Yes | Reflectance values (0.0–1.0 scale) |
| `errors` | ndarray[float64] | No | Measurement uncertainty per band (same units as reflectance) |
| `wavelength_unit` | str | Yes | Always "µm" — enforced at model level |
| `reflectance_unit` | str | Yes | Always "reflectance_factor" (BRDF-normalized where applicable) |
| `n_bands` | int | Yes | Number of spectral channels (len(wavelengths)) |
| `wavelength_range` | tuple[float, float] | Yes | (min_wl, max_wl) in µm |
| `quality` | QualityFlag | Yes | Overall quality assessment |
| `metadata` | SampleMetadata | Yes | Full sample description and provenance |

### SampleMetadata

Comprehensive sample documentation following USGS conventions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `material_name` | str | Yes | Canonical material name |
| `material_category` | MaterialCategory | Yes | Top-level classification |
| `material_subcategory` | str | No | Finer classification within category |
| `formula` | str | No | Chemical formula (minerals) or species binomial (vegetation) |
| `source_library` | SourceLibrary | Yes | Which upstream library this came from |
| `source_record_id` | str | Yes | Original record ID in source library |
| `source_filename` | str | No | Original filename in source distribution |
| `instrument` | str | No | Spectrometer used (e.g., "Beckman 5270", "ASD FieldSpec3") |
| `measurement_type` | MeasurementType | Yes | Lab, field, or airborne |
| `measurement_date` | date | No | When the measurement was taken |
| `grain_size` | str | No | Grain/particle size description |
| `purity` | str | No | Sample purity description |
| `xrd_results` | str | No | X-ray diffraction results summary |
| `em_results` | str | No | Electron microprobe results summary |
| `description` | str | No | Free-text sample description (USGS metadata block) |
| `locality` | str | No | Where sample was collected |
| `geometry` | Point | No | Collection location (WGS84 EPSG:4326) |
| `geometry_ky` | Point | No | Collection location (EPSG:3089) — KY data only |
| `citation` | str | No | Publication reference |
| `license` | str | Yes | Data license (e.g., "US Public Domain", "CC0", "CC-BY-4.0") |
| `ingested_at` | datetime | Yes | When this record was added to speclib |
| `adapter_version` | str | Yes | Version of the ingestion adapter used |

### Enumerations

#### QualityFlag
```
VERIFIED  — Lab-verified purity, high SNR, full wavelength coverage
GOOD      — Reliable measurement, minor issues noted
FAIR      — Usable but with caveats (partial coverage, moderate noise)
POOR      — Significant quality issues, use with caution
SUSPECT   — Known problems, included for completeness only
DERIVED   — Computed from imagery, not direct measurement
```

#### MaterialCategory
```
MINERAL           — Pure minerals and mineral groups
ROCK              — Rock samples (whole rock spectra)
SOIL              — Soil samples and soil types
VEGETATION        — Plant spectra (leaf, canopy, community)
VEGETATION_PLOT   — Field/airborne spectra of vegetation communities
WATER             — Liquid water, ice, snow
MANMADE           — Synthetic and manufactured materials
MIXTURE           — Physical or mathematical mixtures
ORGANIC           — Organic compounds and biochemicals
VOLATILE          — Frozen volatiles, gases
KY_INVASIVE       — Kentucky invasive species (Lyons et al. 2024)
KY_MINERAL        — Kentucky-specific mineral samples
KY_RECLAMATION    — Mine reclamation substrate spectra
```

#### SourceLibrary
```
USGS_SPLIB07      — USGS Spectral Library Version 7
ECOSTRESS         — ECOSTRESS Spectral Library
ASTER_JPL         — ASTER/JPL Spectral Library
EMIT_L2B          — EMIT Level 2B Mineral Identification
KY_FIELD          — Kentucky field measurements (Lyons et al.)
CUSTOM            — User-provided spectra
```

#### MeasurementType
```
LABORATORY        — Controlled lab measurement
FIELD             — Field spectrometer measurement
AIRBORNE          — Airborne imaging spectrometer (AVIRIS, HyMap, etc.)
SPACEBORNE        — Satellite imaging spectrometer (EMIT, Hyperion, etc.)
COMPUTED          — Mathematically derived (mixture modeling, etc.)
```

## Storage Schemas

### HDF5 Attribute Schema

Each spectrum dataset in HDF5 carries these attributes:

```python
{
    "spectrum_id": "usgs_mineral_quartz_a1b2c3d4",
    "name": "Quartz GDS32 med-coarse grain",
    "material_name": "Quartz",
    "material_category": "MINERAL",
    "material_subcategory": "Tectosilicate",
    "formula": "SiO2",
    "source_library": "USGS_SPLIB07",
    "source_record_id": "splib07a_Quartz_GDS32",
    "instrument": "Beckman 5270",
    "measurement_type": "LABORATORY",
    "quality": "VERIFIED",
    "wavelength_unit": "µm",
    "reflectance_unit": "reflectance_factor",
    "n_bands": 481,
    "wavelength_min": 0.2,
    "wavelength_max": 3.0,
    "grain_size": "74-250 µm",
    "purity": ">99% quartz by XRD",
    "license": "US Public Domain",
    "ingested_at": "2026-04-02T12:00:00Z",
    "adapter_version": "0.1.0"
}
```

### Parquet Catalog Schema

Lightweight metadata-only index for fast search:

| Column | Arrow Type | Description |
|--------|-----------|-------------|
| `spectrum_id` | string | Primary key |
| `name` | string | Human-readable name |
| `material_name` | string | Canonical material name |
| `material_category` | string | Category enum value |
| `material_subcategory` | string | Finer classification |
| `formula` | string | Chemical formula / species |
| `source_library` | string | Source enum value |
| `source_record_id` | string | Original ID |
| `instrument` | string | Spectrometer |
| `measurement_type` | string | Measurement type enum |
| `quality` | string | Quality flag enum |
| `n_bands` | int32 | Band count |
| `wavelength_min` | float64 | Min wavelength (µm) |
| `wavelength_max` | float64 | Max wavelength (µm) |
| `locality` | string | Collection location text |
| `geometry` | binary (WKB) | Point geometry (GeoParquet) |
| `citation` | string | Publication reference |

### Parquet Spectra Schema

Full spectral data for query/export:

| Column | Arrow Type | Description |
|--------|-----------|-------------|
| `spectrum_id` | string | Foreign key to catalog |
| `wavelengths` | list\<float64\> | Wavelength array |
| `reflectance` | list\<float64\> | Reflectance array |
| `errors` | list\<float64\> | Error array (nullable) |

### Static JSON Schema

Individual spectrum file (e.g., `spectra/quartz_GDS32_a1b2c3d4.json`):

```json
{
    "spectrum_id": "usgs_mineral_quartz_a1b2c3d4",
    "name": "Quartz GDS32 med-coarse grain",
    "category": "MINERAL",
    "source": "USGS_SPLIB07",
    "quality": "VERIFIED",
    "formula": "SiO2",
    "wavelengths": [0.2, 0.201, ...],
    "reflectance": [0.05, 0.051, ...],
    "metadata": {
        "instrument": "Beckman 5270",
        "grain_size": "74-250 µm",
        "purity": ">99% quartz by XRD",
        "citation": "Kokaly et al. 2017"
    }
}
```

Catalog index (`catalog.json`):

```json
{
    "version": "0.1.0",
    "generated": "2026-04-02T12:00:00Z",
    "count": 5000,
    "categories": { "MINERAL": 1200, "VEGETATION": 800, ... },
    "spectra": [
        {
            "id": "usgs_mineral_quartz_a1b2c3d4",
            "name": "Quartz GDS32 med-coarse grain",
            "category": "MINERAL",
            "source": "USGS_SPLIB07",
            "quality": "VERIFIED",
            "bands": 481,
            "wl_range": [0.2, 3.0],
            "file": "spectra/quartz_GDS32_a1b2c3d4.json"
        }
    ]
}
```

## Sensor Response Functions

Stored as YAML in `data/sensors/`:

```yaml
# data/sensors/landsat8_oli.yaml
name: Landsat 8 OLI
sensor_id: L8_OLI
channels:
  - band: 1
    name: Coastal/Aerosol
    center_wavelength: 0.443
    fwhm: 0.016
  - band: 2
    name: Blue
    center_wavelength: 0.482
    fwhm: 0.060
  # ... etc
response_type: gaussian  # or "tabulated" with explicit RSR arrays
```
