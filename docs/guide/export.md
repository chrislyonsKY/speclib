# Export Formats

speclib supports exporting spectra to multiple formats used in remote sensing and spectroscopy workflows.

## Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| **Esri Spectral Library** | `.esl` | ArcGIS-compatible spectral library |
| **ENVI Spectral Library** | `.sli` | ENVI header + binary spectral library |
| **SPECPR** | `.spc` | USGS SPECPR binary format (round-trip compatible) |
| **ASCII** | `.txt` | Tab-delimited wavelength/reflectance pairs |
| **JSON** | `.json` | Structured JSON with metadata |

## Usage

### Python

```python
spectrum = lib.search("quartz")[0]

# Export single spectrum
spectrum.export("quartz.esl", format="esl")
spectrum.export("quartz.sli", format="sli")
spectrum.export("quartz.json", format="json")

# SPECPR — bit-level header compatibility with USGS tools
spectrum.export("quartz.spc", format="specpr")
```

### CLI

```bash
speclib export usgs_mineral_quartz_a1b2c3d4 --format sli --output quartz.sli
speclib export usgs_mineral_quartz_a1b2c3d4 --format specpr --output quartz.spc
```

## SPECPR Compatibility

The SPECPR exporter produces binary files that round-trip with USGS SPECPR tools. Header structure and byte layout match the original USGS implementation for interoperability with PRISM, TETRACORDER, and other USGS software.
