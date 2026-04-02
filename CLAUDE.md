# CLAUDE.md — speclib
> Federated spectral signature library platform with Kentucky-focused collections
> Python 3.11+ · FastAPI · HDF5 · Parquet · D3.js · GPL-3.0

> **Note:** Do not include this file as indexable context. It is the entry point, not a reference doc.

Read this file completely before doing anything.
Then read `ai-dev/architecture.md` for full context.
Then read `ai-dev/guardrails/` for hard constraints.

---

## Context Boundaries

This file is the AI entry point for this project.
Do NOT auto-scan or index the following:
- `ai-dev/`   (read specific files only when instructed)
- `CLAUDE.md` (this file — entry point only)

When a task requires architecture context: read ai-dev/architecture.md explicitly.
When a task requires constraints: read ai-dev/guardrails/ explicitly.

---

## Workflow Protocol

When starting a new task:
1. Read CLAUDE.md (this file)
2. Read ai-dev/architecture.md
3. Read ai-dev/guardrails/ — constraints override all other guidance
4. Read the relevant ai-dev/agents/ file for your role
5. Check ai-dev/decisions/ for prior decisions affecting your work
6. Check ai-dev/skills/ for domain patterns specific to this project

Plan before building. Show the plan. Wait for confirmation before writing code.

---

## Compatibility Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11+ | Minimum supported runtime |
| h5py | ≥3.10 | HDF5 archival storage layer |
| pyarrow | ≥15.0 | Parquet query layer + GeoParquet |
| FastAPI | ≥0.110 | Optional self-hosted API server |
| Jinja2 | ≥3.1 | Server-side templates (API mode) |
| numpy | ≥1.26 | Spectral array operations |
| scipy | ≥1.12 | Spectral convolution/resampling |
| matplotlib | ≥3.8 | Python-side spectral plotting |
| D3.js | v7 | Client-side spectral visualization (web/) |
| netCDF4 | ≥1.6 | EMIT L2B ingestion |

---

## Project Structure

```
speclib/
├── CLAUDE.md                   # This file — AI entry point
├── README.md                   # Human-facing docs with badges
├── LICENSE                     # GPL-3.0-only
├── pyproject.toml              # Package config, dependencies, entry points
├── ai-dev/                     # AI development infrastructure
│   ├── architecture.md         # System design, data flow, module interfaces
│   ├── spec.md                 # Requirements and acceptance criteria
│   ├── field-schema.md         # Spectral data model (critical)
│   ├── agents/                 # Specialized agent configurations
│   ├── decisions/              # Architectural Decision Records
│   ├── skills/                 # Domain-specific patterns
│   └── guardrails/             # Hard constraints (override all)
├── src/speclib/                # Python package source
│   ├── core/                   # Spectrum, Library, Metadata models
│   ├── ingest/                 # Source adapters (USGS, ECOSTRESS, ASTER, EMIT)
│   ├── export/                 # Output formats (.esl, .sli, SPECPR, ASCII, JSON)
│   ├── storage/                # HDF5 archival + Parquet query layers
│   ├── viz/                    # Matplotlib plotting utilities
│   ├── resample/               # Spectral convolution and resampling
│   └── cli.py                  # CLI entry point
├── web/                        # Web interface (dual mode)
│   ├── static/                 # GitHub Pages static viewer (D3.js)
│   └── api/                    # Optional FastAPI self-hosted server
├── data/
│   ├── ky/                     # Kentucky chapter seed data
│   │   └── invasives/          # Lyons et al. 2024 spectral data
│   └── upstream/               # Federated source YAML configs
├── build/                      # Static site generator pipeline
└── tests/                      # pytest test suite
```

---

## Critical Conventions

1. **EPSG:3089** — All spatial references for Kentucky data use Kentucky Single Zone (NAD83)
2. **Standalone** — No dependencies on AbovePy, earthForge, or occulus. This package is self-contained.
3. **Dual storage** — HDF5 is the archival truth; Parquet is the derived query layer. HDF5 → Parquet, never the reverse.
4. **Adapter pattern** — Every upstream source gets its own ingestion adapter inheriting from `BaseAdapter`
5. **USGS provenance** — All ingested USGS data must retain original splib07 record IDs and metadata
6. **Export fidelity** — SPECPR export must round-trip with USGS SPECPR files (bit-level header compat)
7. **Static-first web** — The GitHub Pages viewer must work with zero server dependencies; FastAPI is optional
8. **Spectral units** — Wavelength in micrometers (µm), reflectance as 0.0–1.0 float. No exceptions.
9. **Quality flags** — Every spectrum carries a quality/purity indicator following USGS conventions
10. **Attribution** — All federated spectra must carry provenance metadata back to original source

---

## Architecture Summary

speclib is a federated spectral signature library platform with three layers:

1. **Python package** (`speclib`) — Core data model, ingestion adapters, storage backends, export formatters, resampling engine. Installable via pip. CLI for batch operations.

2. **Static web viewer** (`web/static/`) — D3.js-powered spectral browser served from GitHub Pages. Reads pre-built JSON catalog files generated by the build pipeline. Zero server dependencies.

3. **Optional FastAPI server** (`web/api/`) — Self-hosted API with Jinja templates for power users who want search, filtering, and programmatic access. Reads from Parquet query layer.

Data flows: Upstream sources → Ingestion adapters → HDF5 archive → Parquet query layer → Static JSON (for web) or API responses (for FastAPI).

Detailed design in `ai-dev/architecture.md`.

---

## Hard Constraints

Read `ai-dev/guardrails/` before writing ANY code. Guardrails override all other instructions.

---

## What NOT To Do

- **Do NOT** add AbovePy, earthForge, or occulus as dependencies
- **Do NOT** use ArcPy — this project runs on macOS and Linux
- **Do NOT** hardcode file paths or assume Windows conventions
- **Do NOT** store raw upstream data in git — only configs, adapters, and seed data references
- **Do NOT** modify HDF5 archives from the Parquet layer — HDF5 is the source of truth
- **Do NOT** use pandas for core spectral operations — use numpy directly for performance
- **Do NOT** assume spectral resolution — always check wavelength arrays, never assume uniform spacing
- **Do NOT** strip USGS metadata during ingestion — preserve everything
