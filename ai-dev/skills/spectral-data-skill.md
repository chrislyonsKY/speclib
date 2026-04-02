# Spectral Data Skill

## SPECPR Binary Format

SPECPR files use fixed 1536-byte records. Key details:
- Records 1-2: File header (title, history)
- Data records: IEEE 754 single-precision floats
- Text records: 40-byte title + metadata
- Error records: paired with data records
- Reference: Clark, R.N., 1993, SPECtrum Processing Routines User's Manual Version 3

## USGS splib07a ASCII Format

Column format per file:
- Line 1+: Header with record metadata
- Data lines: wavelength (µm), reflectance, [error]
- Delete values indicated by -1.23e+34
- Wavelength file separate from reflectance file

## Unit Conventions

| Source | Wavelength | Reflectance |
|--------|-----------|-------------|
| USGS splib07 | µm | 0–1 |
| ECOSTRESS | µm | 0–1 |
| ASTER/JPL | µm | 0–1 (some % → divide by 100) |
| EMIT L2B | nm → µm (divide by 1000) | Band depth (not reflectance) |

## Resampling (splib07b method)

1. Cubic-spline interpolate to fine spacing (0.0001 µm)
2. Skip NaN gaps (do not interpolate across them)
3. For each target band: Gaussian convolution with center λ and FWHM
4. Output: resampled reflectance at effective wavelengths
