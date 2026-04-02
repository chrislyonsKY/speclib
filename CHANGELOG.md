# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-04-02

### Fixed
- Added Zenodo DOI (10.5281/zenodo.19390679) to README citation and badges
- Removed stale DOI placeholder note from README
- Fixed library viewer data URL resolution for Zensical docs

## [1.0.0] - 2026-04-02

### Added

- Core data model: Spectrum, SampleMetadata, QualityFlag, MaterialCategory, SourceLibrary
- Ingestion adapters for USGS splib07a (ASCII), ECOSTRESS, ASTER/JPL, and Kentucky field data
- KY Field adapter for CID CI-710 leaf spectrometer (SpectraSnap! CSV format)
- USGS adapter with spectrometer-aware wavelength file matching (ASD, Beckman, Nicolet)
- HDF5 archival storage backend with gzip-4 compression
- Parquet query layer with catalog and per-category spectral data
- Static JSON build pipeline (catalog.json, taxonomy.json, spectra/*.json)
- D3.js spectral library browser integrated into Zensical docs site
- Interactive spectral chart with zoom, pan, crosshair readout, multi-spectra overlay
- Researcher contribution workflow via GitHub PRs with CI validation
- Three-tier quality system: VERIFIED, CURATED, COMMUNITY
- Quality Standards documentation
- Contribution template directory with example CSV and YAML manifest
- CI pipeline: ruff lint + pytest across 3 OS x 3 Python versions
- Codecov coverage reporting and Codacy code quality analysis
- Zenodo DOI integration and CITATION.cff
- Zensical documentation site with 10+ pages deployed to GitHub Pages
- 1,972 spectra from USGS splib07a (2,418 spectra) and KY field data (270 spectra)
- Kentucky invasive species seed data: Amur honeysuckle (Lonicera maackii) from
  Shelby Trails and Raven Run sites (Lyons et al. 2024)
