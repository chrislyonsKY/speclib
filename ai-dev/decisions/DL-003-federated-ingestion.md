# DL-003: Federated Ingestion via Adapter Pattern

**Date:** 2026-04-02
**Status:** Accepted
**Author:** Chris Lyons

## Context

speclib aggregates spectra from four upstream libraries (USGS splib07, ECOSTRESS, ASTER/JPL, EMIT L2B), each with different file formats, metadata schemas, and distribution methods. The system must normalize these into a unified data model while preserving provenance.

## Decision

Each upstream source gets a dedicated ingestion adapter implementing `BaseAdapter`. Adapters handle source-specific parsing and produce normalized `Spectrum` objects. An adapter registry enables discovery and orchestration.

## Alternatives Considered

- **Monolithic parser** — Rejected because mixing format-specific logic makes the codebase brittle and untestable.
- **Plugin system (entry points)** — Considered but deferred. Entry points add complexity for v0.1.0. The adapter pattern is easily promoted to a plugin system later.
- **Direct database ingestion** — Rejected because it couples ingestion to storage format.

## Consequences

- **Enables:** Each adapter is independently testable; new sources added without modifying existing code; adapters can be contributed by the community.
- **Constrains:** Each source requires dedicated development effort. Metadata normalization requires careful taxonomy mapping.
