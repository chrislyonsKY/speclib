"""EMIT spectral library ingestion adapter.

TODO: Implement discover/fetch/normalize for EMIT source.
"""

from __future__ import annotations

from speclib.core.spectrum import Spectrum
from speclib.ingest.base import BaseAdapter, RawSpectrum, SourceRecord


class EmitAdapter(BaseAdapter):
    """Ingestion adapter for the EMIT spectral library."""

    def discover(self) -> list[SourceRecord]:
        """List available spectra from EMIT L2B source."""
        raise NotImplementedError

    def fetch(self, record_id: str) -> RawSpectrum:
        """Retrieve a single raw spectrum from EMIT."""
        raise NotImplementedError

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert EMIT format to internal Spectrum model."""
        raise NotImplementedError
