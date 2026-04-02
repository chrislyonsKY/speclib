# speclib

![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-informational)
![Status](https://img.shields.io/badge/status-1.0.0-green)
[![CI](https://github.com/chrislyonsKY/speclib/actions/workflows/ci.yml/badge.svg)](https://github.com/chrislyonsKY/speclib/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19390679.svg)](https://zenodo.org/doi/10.5281/zenodo.19390679)
[![codecov](https://codecov.io/gh/chrislyonsKY/speclib/graph/badge.svg)](https://codecov.io/gh/chrislyonsKY/speclib)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/f45422a205bb46ff9955f01622d2d6ab)](https://app.codacy.com/gh/chrislyonsKY/speclib/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
![NumPy](https://img.shields.io/badge/numpy-%E2%89%A51.26-013243?logo=numpy)
![HDF5](https://img.shields.io/badge/HDF5-h5py%20%E2%89%A53.10-blue)
![Parquet](https://img.shields.io/badge/parquet-pyarrow%20%E2%89%A515.0-blue)
![D3.js](https://img.shields.io/badge/D3.js-v7-f9a03c?logo=d3.js)

> Federated spectral signature library with Kentucky-focused collections

## Overview

speclib aggregates reflectance spectra from major public spectral libraries into a unified, searchable platform. It provides a Python package for researchers, a static web viewer for discovery, and an optional self-hosted API for power users.

The library federates spectra from **USGS Spectral Library v7**, **ECOSTRESS**, **ASTER/JPL**, and **EMIT L2B**, with a dedicated Kentucky chapter seeded with invasive species spectral data from Lyons et al. (2024).

## Features

- **Federated ingestion** from USGS splib07, ECOSTRESS, ASTER/JPL, and EMIT L2B
- **Dual storage** — HDF5 archival backend + Parquet query layer
- **Export to** .esl (Esri), .sli (ENVI), SPECPR binary, ASCII, JSON
- **Spectral resampling** to Landsat, Sentinel-2, AVIRIS, EMIT, and custom sensors
- **Static web viewer** on GitHub Pages with D3.js interactive spectral plots
- **Optional FastAPI server** with REST API and Jinja templates
- **Kentucky chapter** with invasive species, mineral, and reclamation spectra

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
pip install speclib
```

With optional dependencies:

```bash
pip install speclib[server]    # FastAPI server
pip install speclib[emit]      # EMIT L2B support (netCDF4)
pip install speclib[all]       # Everything including dev tools
```

### Quick Start

```python
from speclib import SpectralLibrary

# Load the library from an HDF5 archive
lib = SpectralLibrary.from_hdf5("speclib_archive.h5")

# Search for quartz spectra
results = lib.search("quartz", category="MINERAL")

# Plot a spectrum
results[0].plot()

# Export to Esri Spectral Library format
results[0].export("quartz.esl", format="esl")

# Resample to Landsat 8 OLI bands
resampled = results[0].resample("L8_OLI")
```

### CLI

```bash
speclib ingest usgs --config data/upstream/usgs_splib07.yaml
speclib search "honeysuckle" --category KY_INVASIVE
speclib export usgs_mineral_quartz_a1b2c3d4 --format sli --output quartz.sli
speclib build
speclib serve
```

## Web Viewer

Browse the spectral library at: **https://chrislyonsKY.github.io/speclib/**

## Data Sources

| Source | License | Description |
|--------|---------|-------------|
| USGS Spectral Library v7 | US Public Domain | Minerals, rocks, soils, vegetation, manmade materials |
| ECOSTRESS Spectral Library | CC0 / Public Domain | Minerals, vegetation, soils, water, manmade |
| ASTER/JPL Spectral Library | NASA Open Data | Minerals, rocks, soils |
| EMIT L2B | NASA Open Data | Spaceborne mineral identification spectra |
| Kentucky Field Data | CC-BY-4.0 | Invasive species spectra (Lyons et al. 2024) |

## Citation

```bibtex
@software{lyons2026speclib,
  author = {Lyons, Chris},
  title = {speclib: Federated Spectral Signature Library},
  year = {2026},
  url = {https://github.com/chrislyonsKY/speclib},
  doi = {10.5281/zenodo.19390679},
  license = {GPL-3.0}
}
```

> **Note:** Replace `XXXXXXX` with the actual Zenodo DOI after the first release is archived.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

GPL-3.0-only — see [LICENSE](LICENSE) for details.
