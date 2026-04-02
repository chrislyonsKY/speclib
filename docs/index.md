# speclib

**Federated spectral signature library with Kentucky-focused collections**

---

speclib aggregates reflectance spectra from major public spectral libraries into a unified, searchable platform. It provides a Python package for researchers, a static web viewer for discovery, and an optional self-hosted API for power users.

## Data Sources

| Source | Coverage | License |
|--------|----------|---------|
| **USGS Spectral Library v7** | Minerals, rocks, soils, vegetation, manmade materials | US Public Domain |
| **ECOSTRESS** | Minerals, vegetation, soils, water, manmade | CC0 / Public Domain |
| **ASTER/JPL** | Minerals, rocks, soils | NASA Open Data |
| **EMIT L2B** | Spaceborne mineral identification spectra | NASA Open Data |
| **Kentucky Field Data** | Invasive species spectra (Lyons et al. 2024) | CC-BY-4.0 |

## Key Features

- **Federated ingestion** from four major spectral libraries plus custom field data
- **Dual storage** — HDF5 archival backend with Parquet query layer
- **Export** to .esl (Esri), .sli (ENVI), SPECPR binary, ASCII, JSON
- **Spectral resampling** to Landsat, Sentinel-2, AVIRIS, EMIT, and custom sensors
- **Interactive web viewer** with D3.js spectral plotting
- **REST API** via optional FastAPI server
- **Kentucky chapter** with invasive species, mineral, and reclamation spectra

## Quick Install

```bash
pip install speclib
```

```python
from speclib import SpectralLibrary

lib = SpectralLibrary.from_hdf5("speclib_archive.h5")
results = lib.search("quartz", category="MINERAL")
results[0].plot()
```

## Architecture

```
Upstream Sources → Ingestion Adapters → HDF5 Archive
    → Parquet Query Layer → Static JSON / API Responses
```

[Get started](getting-started.md){ .md-button .md-button--primary }
[Browse the Library](library.md){ .md-button }
[View on GitHub](https://github.com/chrislyonsKY/speclib){ .md-button }
