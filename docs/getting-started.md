# Getting Started

## Prerequisites

- Python 3.11 or later
- pip

## Installation

Install the base package:

```bash
pip install speclib
```

Install with optional extras:

```bash
pip install speclib[server]    # FastAPI server
pip install speclib[emit]      # EMIT L2B support (netCDF4)
pip install speclib[all]       # Everything including dev tools
```

### Development Installation

```bash
git clone https://github.com/chrislyonsKY/speclib.git
cd speclib
pip install -e ".[dev]"
```

## First Steps

### Load a Spectral Library

```python
from speclib import SpectralLibrary

lib = SpectralLibrary.from_hdf5("speclib_archive.h5")
```

### Search for Spectra

```python
# Search by name
results = lib.search("quartz", category="MINERAL")

# Search Kentucky invasive species
invasives = lib.search("honeysuckle", category="KY_INVASIVE")
```

### Plot a Spectrum

```python
spectrum = results[0]
spectrum.plot()
```

### Export

```python
# Esri Spectral Library format
spectrum.export("quartz.esl", format="esl")

# ENVI Spectral Library
spectrum.export("quartz.sli", format="sli")

# SPECPR binary (USGS-compatible)
spectrum.export("quartz.spc", format="specpr")
```

### Resample to a Sensor

```python
# Convolve to Landsat 8 OLI bands
resampled = spectrum.resample("L8_OLI")

# Convolve to Sentinel-2 MSI bands
resampled = spectrum.resample("S2_MSI")
```

## CLI Usage

```bash
# Ingest from USGS Spectral Library v7
speclib ingest usgs --config data/upstream/usgs_splib07.yaml

# Search the library
speclib search "honeysuckle" --category KY_INVASIVE

# Export a spectrum
speclib export usgs_mineral_quartz_a1b2c3d4 --format sli --output quartz.sli

# Build the static web viewer
speclib build

# Start the FastAPI server
speclib serve
```

## Next Steps

- [Spectral Data Model](guide/data-model.md) — understand wavelengths, reflectance, and quality flags
- [Ingestion Guide](guide/ingestion.md) — add spectra from upstream sources
- [Export Formats](guide/export.md) — supported output formats
- [Kentucky Chapter](../kentucky.md) — invasive species and regional collections
