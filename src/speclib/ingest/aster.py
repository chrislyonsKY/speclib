"""ASTER spectral library ingestion adapter.

TODO: Implement discover/fetch/normalize for ASTER source.
"""

from __future__ import annotations

from speclib.core.spectrum import Spectrum
from speclib.ingest.base import BaseAdapter, RawSpectrum, SourceRecord


class AsterAdapter(BaseAdapter):
    """Ingestion adapter for the ASTER spectral library."""

    def discover(self) -> list[SourceRecord]:
        # TODO: Implement
        raise NotImplementedError

    def fetch(self, record_id: str) -> RawSpectrum:
        # TODO: Implement
        raise NotImplementedError

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        # TODO: Implement
        raise NotImplementedError
