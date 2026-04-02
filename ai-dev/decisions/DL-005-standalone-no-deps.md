# DL-005: Standalone Package (No AbovePy/earthForge/occulus Dependencies)

**Date:** 2026-04-02
**Status:** Accepted
**Author:** Chris Lyons

## Context

Chris maintains several interrelated Python packages (AbovePy for STAC, earthForge for pipelines, occulus for LiDAR). speclib could integrate with these but doing so couples speclib's release cycle and user base to the broader ecosystem.

## Decision

speclib is fully standalone with no dependencies on AbovePy, earthForge, or occulus. It uses only standard scientific Python (numpy, scipy, h5py, pyarrow) plus FastAPI for the optional server.

## Alternatives Considered

- **earthForge for GeoParquet I/O** — Rejected to avoid coupling. pyarrow handles GeoParquet natively.
- **AbovePy for EMIT data access** — Rejected. EMIT L2B files are NetCDF4; netCDF4 library handles them directly without STAC indirection.
- **Optional extras** — Considered `pip install speclib[earthforge]` extras, but deferred to avoid maintenance burden at v0.1.0.

## Consequences

- **Enables:** speclib installable in any Python environment without ecosystem buy-in; simpler dependency tree; broader adoption potential.
- **Constrains:** Some code may duplicate patterns available in earthForge (GeoParquet helpers). Users wanting STAC integration use AbovePy separately.
