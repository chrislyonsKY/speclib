# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.1.0] - TBD

### Added
- Initial project scaffold
- Core data model (Spectrum, SampleMetadata, QualityFlag, MaterialCategory)
- Ingestion adapter framework with USGS, ECOSTRESS, ASTER, EMIT adapters
- HDF5 archival storage backend
- Parquet query layer with build pipeline
- Export formats: .esl, .sli, SPECPR, ASCII, JSON
- Spectral resampling engine with Landsat 8 and Sentinel-2 profiles
- CLI interface (ingest, search, export, resample, build, serve)
- Static web viewer with D3.js spectral charts
- Optional FastAPI server with REST API
- Kentucky invasive species seed data (Lyons et al. 2024)
