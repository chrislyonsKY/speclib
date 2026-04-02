# Quality Standards

speclib maintains a tiered quality system to ensure data integrity while welcoming community contributions.

## Quality Tiers

| Tier | Source | Entry Method | Review |
|------|--------|-------------|--------|
| **VERIFIED** | USGS splib07, ECOSTRESS, ASTER/JPL | Automated ingestion from authoritative sources | Peer-reviewed upstream libraries |
| **CURATED** | Maintainer field data (KY chapter) | Direct ingestion by project maintainers | Maintainer-verified instruments and calibration |
| **COMMUNITY** | Researcher contributions | GitHub PR with validation | CI format checks + maintainer credential review |

## Data Requirements

All spectral data in speclib must meet these minimum standards regardless of tier:

### Calibration

- **Calibrated reflectance only** — all spectra must be calibrated against a known reference standard
- Raw DN values, uncalibrated measurements, and transmission spectra are not accepted
- Contributors must document their calibration method (e.g., Spectralon white reference panel, vicarious calibration, atmospheric correction)
- Reflectance values must be on a 0.0-1.0 scale (fractional, not percentage)

### Wavelength

- Wavelengths must be in micrometers (um)
- Wavelength arrays must be sorted in ascending order
- Non-uniform spacing is acceptable (store as measured, do not resample)

### Metadata

Every spectrum must carry:

- **Material name** and **category** classification
- **Source library** identifier and **original record ID**
- **Measurement type** (laboratory, field, airborne, spaceborne)
- **License** for data use
- **Instrument** used for measurement

### Spectral Integrity

- Spectral gaps are stored as `NaN`, never interpolated
- Out-of-range reflectance values (outside 0.0-1.0) are flagged with a warning, never silently clipped
- Delete values from upstream sources (e.g., USGS `-1.23e+34`) are converted to `NaN`

## Contribution Review Process

Community contributions go through a two-stage review:

### Stage 1: Automated Validation (CI)

The CI pipeline automatically checks:

- `contribution.yaml` has all required fields
- `calibrated: true` is set
- `calibration_method` is non-empty
- Contributor `affiliation` and `email` are provided
- CSV data parses correctly
- Wavelengths are sorted ascending
- Reflectance values are in [0.0, 1.0]
- Wavelength and reflectance arrays are the same length

### Stage 2: Maintainer Review

A project maintainer manually verifies:

- **Contributor credentials** — institutional affiliation is legitimate
- **Instrument and calibration** — measurement setup is appropriate for the claimed data
- **Data quality** — spectra look physically reasonable (no obvious artifacts, saturation, or noise issues)
- **Metadata completeness** — description, locality, and citation are adequate
- **License compatibility** — data license is compatible with the project (GPL-3.0 for code, CC-BY-4.0 recommended for data)

### Promotion

After merging, community contributions remain in the `COMMUNITY` tier. A maintainer can promote contributions to `CURATED` status after additional verification (e.g., comparing against known reference spectra, confirming measurement conditions).

## Instruments

speclib accepts data from any calibrated spectrometer or imaging spectrometer. Common instruments include:

| Instrument | Type | Typical Range |
|-----------|------|--------------|
| ASD FieldSpec (3/4) | Portable field spectrometer | 0.35-2.5 um |
| CID CI-710 | Leaf spectrometer | 0.40-0.95 um |
| Spectral Evolution PSR+ | Portable spectrometer | 0.35-2.5 um |
| Ocean Optics USB series | Compact spectrometer | 0.20-1.1 um |
| AVIRIS / AVIRIS-NG | Airborne imaging spectrometer | 0.38-2.5 um |
| HyMap | Airborne imaging spectrometer | 0.45-2.5 um |
| EMIT | Spaceborne imaging spectrometer | 0.38-2.5 um |

Drone-mounted spectrometers and hyperspectral cameras are welcome as long as the data has been radiometrically calibrated and atmospherically corrected.
