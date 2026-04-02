"""Base adapter interface for spectral library ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from speclib.core.spectrum import Spectrum


@dataclass
class SourceRecord:
    """A discoverable record in an upstream source."""

    record_id: str
    name: str
    category: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RawSpectrum:
    """Unparsed spectral data in source-native format."""

    record_id: str
    wavelengths: Any
    reflectance: Any
    wavelength_unit: str
    reflectance_scale: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """Abstract base class for all ingestion adapters.

    Subclasses implement: discover → fetch → normalize.
    """

    def __init__(self, config_path: Path) -> None:
        """Initialize adapter with a YAML configuration file path."""
        self.config_path = config_path
        # TODO: Load YAML config

    @abstractmethod
    def discover(self) -> list[SourceRecord]:
        """List available spectra from the upstream source."""
        ...

    @abstractmethod
    def fetch(self, record_id: str) -> RawSpectrum:
        """Retrieve a single raw spectrum with metadata."""
        ...

    @abstractmethod
    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert source-native format to internal Spectrum model."""
        ...

    def ingest_all(self) -> list[Spectrum]:
        """Run full ingestion pipeline for all discoverable spectra."""
        return [self.normalize(self.fetch(r.record_id)) for r in self.discover()]
