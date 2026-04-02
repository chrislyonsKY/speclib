# Data Handling Guardrails

## Provenance

- NEVER strip or modify upstream metadata during ingestion — preserve everything
- Every spectrum must carry `source_library` and `source_record_id` back to its origin
- The `ingested_at` timestamp and `adapter_version` must be set automatically, never manually
- If upstream metadata fields are missing, store as null — never fabricate values

## Spectral Data Integrity

- Wavelength unit is ALWAYS micrometers (µm) — convert on ingestion if source uses nm or cm⁻¹
- Reflectance scale is ALWAYS 0.0–1.0 — convert on ingestion if source uses percent (0–100)
- NEVER interpolate or modify spectral data during ingestion — store as measured
- Resampling is a separate, explicit operation — never done implicitly during storage
- SPECPR binary export must preserve original header structure for USGS tool compatibility

## Spatial Data

- Kentucky data: EPSG:3089 (Kentucky Single Zone, NAD83)
- All other spatial data: EPSG:4326 (WGS84)
- GeoParquet geometry column uses WKB encoding
- Coordinate precision: 6 decimal places for lat/lon, 2 decimal places for projected coords

## Storage

- HDF5 is the single source of truth — Parquet and JSON are derived and regenerable
- NEVER write to HDF5 from the Parquet layer or web interface
- HDF5 datasets use gzip compression (level 4) by default
- Parquet files use snappy compression

## Credentials & Secrets

- NEVER hardcode API keys, tokens, or credentials in source code
- Configuration files containing paths or credentials must be in .gitignore
- Upstream source URLs go in YAML config files, not hardcoded in adapter code

## Git & Large Files

- Do NOT commit spectral data files (HDF5, Parquet, SPECPR binary) to git
- Do NOT commit upstream source distributions to git
- Seed data references (YAML configs pointing to source files) ARE committed
- The `data/` directory is in .gitignore except for YAML configs and the KY seed data manifest
