# DL-002: Static Hybrid API Architecture

**Date:** 2026-04-02
**Status:** Accepted
**Author:** Chris Lyons

## Context

speclib needs both broad accessibility (anyone can browse spectra in a browser) and power-user capabilities (programmatic search, filtering, batch export). Hosting a live server has ongoing cost; USGS distributes data as static files.

## Decision

Hybrid architecture: GitHub Pages serves a static D3.js viewer reading pre-built JSON files, and an optional self-hosted FastAPI server provides REST API + Jinja templates for power users. The Python package works independently of both.

## Alternatives Considered

- **Server-only (FastAPI on Render/DO)** — Rejected because ongoing hosting cost contradicts the USGS public-domain distribution ethos. Also creates a single point of failure.
- **Static-only (GitHub Pages)** — Rejected because static JSON limits search sophistication and can't support spectral matching or server-side resampling.
- **SPA framework (React/Vue)** — Rejected as overengineered for a data-first spectral browser. D3.js gives full control over spectral chart rendering without framework overhead.

## Consequences

- **Enables:** Zero-cost distribution via GitHub Pages; optional self-hosting for institutions; Python package works offline.
- **Constrains:** Static viewer limited to client-side search over pre-built JSON. Build pipeline must generate the static catalog. Large libraries may need paginated JSON loading.
