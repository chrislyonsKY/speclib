# Ingestion

## Adapter Pattern

Each upstream spectral library has a dedicated adapter inheriting from `BaseAdapter`. Adapters handle source-specific formats and normalize data to speclib's internal model.

## Supported Sources

### USGS Spectral Library v7

```bash
speclib ingest usgs --config data/upstream/usgs_splib07.yaml
```

Parses splib07a ASCII files and SPECPR binary format. Preserves original record numbers and chapter codes.

### ECOSTRESS

```bash
speclib ingest ecostress --config data/upstream/ecostress.yaml
```

Reads ECOSTRESS spectral library CSV and HDF5 files. Maps ECOSTRESS categories to speclib taxonomy.

### ASTER/JPL

```bash
speclib ingest aster --config data/upstream/aster_jpl.yaml
```

Reads ASTER/JPL spectral library files with JPL-specific header format handling.

### EMIT L2B

Requires the `emit` extra:

```bash
pip install speclib[emit]
speclib ingest emit --config data/upstream/emit_l2b.yaml
```

Extracts per-pixel mineral spectra with geolocation from EMIT L2B NetCDF4 granules.

## Configuration

Upstream sources are configured via YAML files in `data/upstream/`. Each config specifies:

```yaml
source:
  name: "USGS Spectral Library v7"
  version: "splib07a"
  url: "https://crustal.usgs.gov/speclab/QueryAll07a.php"

adapter:
  class: "USGSAdapter"

paths:
  data_dir: "/path/to/splib07a"
  output_archive: "speclib_archive.h5"
```

## Writing Custom Adapters

Implement the `BaseAdapter` interface:

```python
from speclib.ingest.base import BaseAdapter, RawSpectrum, SourceRecord
from speclib.core import Spectrum

class MyAdapter(BaseAdapter):
    def discover(self) -> list[SourceRecord]:
        """List available spectra from the source."""
        ...

    def fetch(self, record_id: str) -> RawSpectrum:
        """Retrieve a single raw spectrum with metadata."""
        ...

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert to speclib's internal Spectrum model."""
        ...
```
