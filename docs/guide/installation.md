# Installation

## Requirements

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| pip | Latest recommended |

## Package Installation

### Base Package

```bash
pip install speclib
```

Core dependencies installed automatically:

- `numpy` >= 1.26 — spectral array operations
- `scipy` >= 1.12 — spectral convolution and resampling
- `h5py` >= 3.10 — HDF5 archival storage
- `pyarrow` >= 15.0 — Parquet query layer
- `click` >= 8.1 — CLI framework
- `pyyaml` >= 6.0 — configuration files
- `matplotlib` >= 3.8 — spectral plotting

### Optional Extras

```bash
# FastAPI server for REST API and web interface
pip install speclib[server]

# EMIT L2B NetCDF4 support
pip install speclib[emit]

# Development tools (pytest, ruff, pre-commit)
pip install speclib[dev]

# Everything
pip install speclib[all]
```

## Development Setup

```bash
git clone https://github.com/chrislyonsKY/speclib.git
cd speclib
pip install -e ".[all]"
```

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

## Verifying Installation

```python
import speclib
print(speclib.__version__)
```
