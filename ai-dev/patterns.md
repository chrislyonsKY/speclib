# Code Patterns — speclib

## Adapter Pattern (Ingestion)

All ingestion adapters follow the three-step pipeline:
```python
adapter = UsgsAdapter(config_path=Path("data/upstream/usgs_splib07.yaml"))
records = adapter.discover()       # Step 1: enumerate
raw = adapter.fetch(records[0].record_id)  # Step 2: retrieve raw
spectrum = adapter.normalize(raw)   # Step 3: normalize to Spectrum
```

## Storage Hierarchy

```
HDF5 (source of truth) → Parquet (query layer) → JSON (static web)
         ↑ write only        ↑ read only            ↑ read only
```

## Anti-Patterns

- NEVER read Parquet and write back to HDF5
- NEVER assume uniform wavelength spacing
- NEVER use pandas in core modules (numpy + pyarrow only)
- NEVER interpolate spectral data during ingestion
- NEVER hardcode file paths (use pathlib + config)
