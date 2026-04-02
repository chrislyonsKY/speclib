"""ECOSTRESS spectral library ingestion adapter.

TODO: Implement discover/fetch/normalize for ECOSTRESS source.
"""

from __future__ import annotations

from speclib.core.spectrum import Spectrum
from speclib.ingest.base import BaseAdapter, RawSpectrum, SourceRecord


class EcostressAdapter(BaseAdapter):
    """Ingestion adapter for the ECOSTRESS spectral library."""

    def discover(self) -> list[SourceRecord]:
        """List available spectra from ECOSTRESS source."""
        raise NotImplementedError

    def fetch(self, record_id: str) -> RawSpectrum:
        """Retrieve a single raw spectrum from ECOSTRESS."""
        raise NotImplementedError

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert ECOSTRESS format to internal Spectrum model."""
        raise NotImplementedError
