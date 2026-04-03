# Compliance Guardrails

## Licensing & Attribution

- speclib software: GPL-3.0-only
- USGS data: US Public Domain — attribute as "U.S. Geological Survey, Spectral Library Version 7"
- ECOSTRESS data: Check license per dataset — most are CC0 or public domain
- ASTER/JPL data: Check JPL distribution terms — typically unrestricted with attribution
- EMIT data: NASA open data policy — attribute as "NASA/JPL EMIT Mission"
- All exported files must include a provenance/attribution block in metadata
- Kentucky field data (Lyons, Gyawali, Cristan, Acharya, Gebremedhin, & Andries, 2024): Cite as published — include DOI 10.1080/01431161.2024.2391095 in metadata

## WCAG 2.1 Level AA (Web Interface)

- Color must never be the sole means of distinguishing spectra in plots — use line styles, markers
- All interactive elements must be keyboard-accessible
- D3.js charts must have ARIA labels and text alternatives
- Minimum contrast ratio 4.5:1 for text, 3:1 for graphical elements
- Focus indicators visible on all interactive elements

## Data Citation

- The web viewer must display citation information for every spectrum
- Exported files must include citation metadata in headers/attributes
- The README must document how to cite speclib itself and upstream data sources
- BibTeX entries provided for speclib and each upstream source

## Open Source

- All source code commits must be compatible with GPL-3.0-only
- No proprietary dependencies (no ENVI license required, no IDL required)
- SPECPR/PRISM compatibility achieved through clean-room implementation, not wrapping proprietary code
