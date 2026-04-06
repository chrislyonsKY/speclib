<div align="center">

<br>

# speclib

### The Open Spectral Signature Library

*5,900+ reference spectra. Interactive comparison. Sensor band overlays.*
*Python, Rust, and R. Built for researchers who need more than a static table.*

<br>

[![License](https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/speclib?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/speclib/)
[![CI](https://img.shields.io/github/actions/workflow/status/chrislyonsKY/speclib/ci.yml?style=flat-square&logo=github&label=CI)](https://github.com/chrislyonsKY/speclib/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/1199662773.svg)](https://doi.org/10.5281/zenodo.19390678)
[![codecov](https://img.shields.io/codecov/c/gh/chrislyonsKY/speclib?style=flat-square&logo=codecov&logoColor=white)](https://codecov.io/gh/chrislyonsKY/speclib)
[![Codacy](https://img.shields.io/codacy/grade/f45422a205bb46ff9955f01622d2d6ab?style=flat-square&logo=codacy&logoColor=white)](https://app.codacy.com/gh/chrislyonsKY/speclib/dashboard)

[![Rust](https://img.shields.io/badge/Rust-speclib--core-DEA584?style=flat-square&logo=rust&logoColor=white)](speclib-rs/)
[![Plotly.js](https://img.shields.io/badge/Plotly.js-v2.35-3F4F75?style=flat-square&logo=plotly&logoColor=white)](https://plotly.com/javascript/)
[![NumPy](https://img.shields.io/badge/NumPy-%E2%89%A51.26-013243?style=flat-square&logo=numpy&logoColor=white)](https://numpy.org)
[![HDF5](https://img.shields.io/badge/HDF5-h5py%20%E2%89%A53.10-0075B8?style=flat-square)](https://www.hdfgroup.org/)
[![Parquet](https://img.shields.io/badge/Parquet-pyarrow%20%E2%89%A515.0-50ABF1?style=flat-square&logo=apache&logoColor=white)](https://arrow.apache.org/)

<br>

[**Launch Viewer**](https://chrislyonsKY.github.io/speclib/) | [**Install**](#installation) | [**Docs**](https://chrislyonsKY.github.io/speclib/docs/) | [**Cite**](#citation)

<br>

</div>

---

## Why speclib?

Existing spectral libraries ship as flat files, locked behind clunky viewers, or require proprietary software. **speclib** changes that:

| | USGS Spectra Viewer | JPL ECOSTRESS | **speclib** |
|---|---|---|---|
| Interactive chart | | | Plotly.js zoom/pan/crosshair |
| Compare spectra | | side-by-side only | Up to 6 overlaid traces |
| Sensor band overlay | | | Landsat 8/9, Sentinel-2 |
| Absorption annotations | | | Fe, Al-OH, H2O, CO3, Chl |
| Export from viewer | | | CSV + PNG |
| Shareable URLs | | | Permalink any comparison |
| Dark mode | | | System-aware |
| Federated sources | USGS only | ECOSTRESS only | USGS + ECOSTRESS + ASTER + EMIT + field data |
| Multi-language | | | Python, Rust, R (planned) |
| Python API | | | `pip install speclib` |
| Self-hostable | | | Optional FastAPI server |
| Open source | | | GPL-3.0 |

## What's Inside

**5,900+ spectra** across 12 categories from 3 federated sources:

| Category | Count | Source | Instruments |
|----------|------:|--------|------------|
| **Minerals** | 2,880 | USGS + ECOSTRESS | ASD, Beckman, Nicolet, Perkin-Elmer |
| **Vegetation** | 1,332 | USGS + ECOSTRESS | ASD FieldSpec, Beckman, AVIRIS |
| **Rocks** | 470 | ECOSTRESS | ASD, Beckman, Nicolet, Perkin-Elmer |
| **Organic Compounds** | 359 | USGS splib07a | ASD FieldSpec HR, Nicolet FTIR |
| **Artificial Materials** | 290 | USGS splib07a | ASD FieldSpec, Beckman |
| **Soils** | 278 | USGS + ECOSTRESS | ASD, Beckman, Nicolet |
| **KY Invasive Species** | 136 | Lyons et al. (2024) | CID CI-710 (Ocean Optics USB4000) |
| **Non-Photosynthetic Vegetation** | 117 | ECOSTRESS | ASD FieldSpec, Nicolet FTIR |
| **Liquids** | 24 | USGS splib07a | ASD FieldSpec, Beckman |
| **Coatings & Mixtures** | 24 | USGS splib07a | Beckman 5270 |

### Kentucky Chapter

The library includes field-collected spectral data from Lyons, Gyawali, Cristan, Acharya, Gebremedhin, & Andries (2024) targeting **invasive species detection** in Kentucky:

- **Amur honeysuckle** (*Lonicera maackii*) — 136 leaf reflectance spectra across canopy positions (upper/mid/lower) from Raven Run and Shelby Trails sites
- Measured with CID CI-710 leaf spectrometer (345 - 1,035 nm, 3,648 bands)
- All spatial references in **EPSG:3089** (Kentucky Single Zone, NAD83)
- Licensed CC-BY-4.0

## Web Viewer

**[Launch the viewer](https://chrislyonsKY.github.io/speclib/)** — no install, no login, no server.

### Key capabilities

- **Real-time search** across 5,900+ spectra with instant filtering by category, instrument, and measurement type
- **Multi-spectra comparison** — overlay up to 6 spectra with WCAG-compliant distinct line styles and colorblind-safe palette
- **Sensor band overlays** — toggle **Landsat 8/9 OLI** and **Sentinel-2 MSI** band positions directly on the chart (essential for field-to-satellite workflows)
- **Absorption feature markers** — diagnostic wavelengths for Fe3+, Fe2+, Chlorophyll, H2O, Al-OH, Mg-OH/CO3 annotated on-chart
- **Export** — download any comparison as CSV or publication-ready PNG
- **Permalink sharing** — URL encodes your exact view (spectra selection, category, search query)
- **Dark/light mode** — respects system preference, toggleable
- **Keyboard accessible** — press `/` to focus search, full keyboard navigation

## Python Package

### Installation

```bash
pip install speclib
```

```bash
pip install speclib[server]    # FastAPI server
pip install speclib[emit]      # EMIT L2B support (netCDF4)
pip install speclib[all]       # Everything
```

### Quick Start

```python
from speclib import SpectralLibrary

lib = SpectralLibrary.from_hdf5("speclib_archive.h5")

# Search
results = lib.search("quartz", category="MINERAL")

# Plot
results[0].plot()

# Export to Esri / ENVI / SPECPR
results[0].export("quartz.esl", format="esl")

# Resample to Landsat 8 OLI bands
resampled = results[0].resample("L8_OLI")
```

### CLI

```bash
speclib ingest usgs --config data/upstream/usgs_splib07.yaml
speclib search "honeysuckle" --category KY_INVASIVE
speclib export <spectrum_id> --format sli --output quartz.sli
speclib build    # Generate static JSON for the web viewer
speclib serve    # Launch optional FastAPI server
```

## Rust Crate

The `speclib-core` Rust crate provides native access to the spectral library with no Python dependency. JSON and Parquet I/O, core types, and deterministic ID generation — all implementing the same [format specification](docs/format-spec.md).

```rust
use speclib_core::json::{read_catalog, read_spectrum};
use speclib_core::Spectrum;

let catalog = read_catalog("data/catalog.json".as_ref())?;
let spectrum = read_spectrum("data/spectra/quartz.json".as_ref())?;
println!("{}: {} bands", spectrum.name, spectrum.n_bands());
```

**Planned:** CLI (`speclib-cli`), WASM for browser-side spectral operations (`speclib-wasm`), HDF5 read/write (feature-gated).

## Architecture

```
Upstream Sources          Storage Layer              Distribution Layer
┌──────────────┐     ┌───────────────────┐     ┌──────────────────────┐
│  USGS splib07 │────>│                   │     │  GitHub Pages Viewer │
│  ECOSTRESS    │────>│  HDF5 Archive     │────>│  (Plotly.js + JSON)  │
│  ASTER/JPL    │────>│  (source of truth)│     ├──────────────────────┤
│  EMIT L2B     │────>│        │          │     │  FastAPI Server      │
│  KY Field     │────>│        v          │     │  (optional, Parquet) │
└──────────────┘     │  Parquet Query    │────>│  REST API + Jinja    │
                      └───────────────────┘     └──────────────────────┘
                                                         │
                      Language Bindings                   │
                      ┌───────────────────┐              │
                      │  speclib-core (Rust)│<── JSON/Parquet
                      │  speclib (R)       │   (format spec v1.0)
                      └───────────────────┘
```

- **HDF5** is the archival source of truth (gzip-4 compressed, hierarchical)
- **Parquet** is the derived query layer (columnar, fast filtering, GeoParquet for spatial)
- **Static JSON** powers the zero-dependency GitHub Pages viewer
- Each upstream source has a dedicated **ingestion adapter** inheriting from `BaseAdapter`
- **Rust and R** implement the same [format specification](docs/format-spec.md) independently

## Resampling

Convolve any library spectrum to match target sensor bandpasses:

| Sensor | Bands | Range |
|--------|------:|-------|
| Landsat 8/9 OLI | 7 | 0.43 - 2.29 µm |
| Sentinel-2 MSI | 13 | 0.44 - 2.19 µm |
| AVIRIS-Classic | 224 | 0.37 - 2.50 µm |
| AVIRIS-NG | 425 | 0.38 - 2.51 µm |
| EMIT | 285 | 0.38 - 2.50 µm |
| ASD FieldSpec | 2,151 | 0.35 - 2.50 µm |
| Custom | user-defined | user-defined |

## Data Provenance

| Source | License | Attribution |
|--------|---------|-------------|
| **USGS Spectral Library v7** | US Public Domain | Kokaly, R.F., et al., 2017, USGS Spectral Library Version 7 |
| **ECOSTRESS** | CC0 / Public Domain | Baldridge, A.M., et al., 2009, ECOSTRESS spectral library |
| **ASTER/JPL** | NASA Open Data | Jet Propulsion Laboratory, California Institute of Technology |
| **EMIT L2B** | NASA Open Data | NASA/JPL EMIT Mission |
| **KY Field Data** | CC-BY-4.0 | Lyons, W. C., Gyawali, B. R., Cristan, R., Acharya, S., Gebremedhin, M., & Andries, K. (2024). *Int. J. Remote Sensing*, 45(18), 6470–6494. [doi:10.1080/01431161.2024.2391095](https://doi.org/10.1080/01431161.2024.2391095) |

## Citation

```bibtex
@software{lyons2026speclib,
  author       = {Lyons, Chris},
  title        = {speclib: Federated Spectral Signature Library},
  year         = {2026},
  publisher    = {Zenodo},
  url          = {https://github.com/chrislyonsKY/speclib},
  doi          = {10.5281/zenodo.19390679},
  license      = {GPL-3.0}
}
```

## Contributing

We welcome community spectral contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow, and [Quality Standards](docs/guide/quality-standards.md) for submission criteria.

## License

GPL-3.0-only — see [LICENSE](LICENSE).
