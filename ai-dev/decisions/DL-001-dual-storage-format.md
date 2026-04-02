# DL-001: Dual Storage Format (HDF5 + Parquet)

**Date:** 2026-04-02
**Status:** Accepted
**Author:** Chris Lyons

## Context

speclib needs a storage backend that supports both archival integrity (preserving full spectral arrays with hierarchical metadata) and fast analytical queries (search, filter, catalog browsing). No single format optimally serves both needs.

## Decision

Use HDF5 as the archival source of truth and Parquet as the derived query layer. A build pipeline transforms HDF5 → Parquet. The Parquet layer is always regenerable from HDF5.

## Alternatives Considered

- **HDF5 only** — Rejected because HDF5 is poor for columnar queries, filtering, and integration with data lake tooling. Would make the API layer slow.
- **Parquet only** — Rejected because Parquet is flat/columnar and poorly suited for hierarchical scientific data with per-record metadata attributes. Loses the self-describing nature needed for archival.
- **SQLite/SpatiaLite** — Rejected because BLOB storage for spectral arrays is awkward, and SQLite doesn't match the scientific data ecosystem. Also no standard spatial extension interop with GeoParquet.
- **NetCDF4** — Considered (it's HDF5-based), but raw HDF5 gives more control over hierarchy and attributes without CF convention overhead.

## Consequences

- **Enables:** Fast catalog queries via Parquet; rich archival storage via HDF5; static JSON generation from Parquet for GitHub Pages; GeoParquet spatial queries for EMIT/field data.
- **Constrains:** Requires a build pipeline step between ingestion and query. Two storage layers to maintain. HDF5 → Parquet direction is enforced (never reverse).
