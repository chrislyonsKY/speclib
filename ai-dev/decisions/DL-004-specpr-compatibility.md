# DL-004: Full SPECPR Binary Compatibility

**Date:** 2026-04-02
**Status:** Accepted
**Author:** Chris Lyons

## Context

The USGS Spectral Library uses SPECPR binary format as its native storage. Researchers using USGS tools (SPECPR CLI, PRISM IDL) expect binary-compatible files. Round-trip fidelity is essential for credibility.

## Decision

Implement custom SPECPR binary reader/writer in Python that produces bit-level header-compatible files. The export must round-trip with USGS SPECPR reference files.

## Alternatives Considered

- **ASCII-only support** — Rejected because SPECPR binary is the canonical USGS format and many workflows depend on it.
- **Wrap existing SPECPR tools** — Rejected because SPECPR/PRISM are IDL-based and would add a heavy non-Python dependency.
- **pysptools SPECPR support** — Investigated but pysptools does not provide full SPECPR write capability.

## Consequences

- **Enables:** Full interoperability with USGS tooling; speclib can serve as a modern Python frontend for SPECPR data.
- **Constrains:** SPECPR binary format is complex (fixed-record, mixed binary/text headers). Requires careful testing against reference files. The SPECPR format spec (Clark, 1993) must be followed precisely.
