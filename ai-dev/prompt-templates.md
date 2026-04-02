# Prompt Templates — speclib

## Implement Ingestion Adapter

```
Read CLAUDE.md, then ai-dev/architecture.md, then ai-dev/agents/spectral_expert.md.

Implement the [SOURCE] ingestion adapter in src/speclib/ingest/[source].py.

The adapter must:
1. Parse [SOURCE FORMAT DESCRIPTION]
2. Normalize to speclib Spectrum model (see ai-dev/field-schema.md)
3. Preserve all upstream metadata
4. Convert units: wavelength to µm, reflectance to 0-1 fraction
5. Assign QualityFlags based on source metadata
6. Generate deterministic spectrum_id

Reference: [SOURCE DOCUMENTATION LINK]

Write tests in tests/test_ingest.py using sample data files.
```

## Implement Export Format

```
Read CLAUDE.md, then ai-dev/agents/spectral_expert.md, then ai-dev/skills/spectral-data-skill.md.

Implement the [FORMAT] exporter in src/speclib/export/[format].py.

Requirements:
1. write() for single spectrum, batch_write() for multiple
2. Output must be readable by [TARGET SOFTWARE]
3. Include metadata/provenance in format-appropriate headers
4. Write round-trip test: write → read → compare arrays (numpy.isclose)
```
