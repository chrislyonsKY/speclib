"""Base adapter interface for spectral library ingestion."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from speclib.core.spectrum import Spectrum

logger = logging.getLogger(__name__)


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

    Subclasses implement: discover -> fetch -> normalize.
    """

    def __init__(self, config_path: Path) -> None:
        """Initialize adapter with a YAML configuration file path.

        Args:
            config_path: Path to the YAML configuration file.
        """
        self.config_path = Path(config_path)
        with self.config_path.open() as f:
            self.config: dict[str, Any] = yaml.safe_load(f)
        source = self.config.get("source", "unknown")
        logger.info("Loaded config for %s from %s", source, config_path)

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
        """Run full ingestion pipeline for all discoverable spectra.

        Returns:
            List of normalized Spectrum objects.
        """
        records = self.discover()
        source = self.config.get("source", "unknown")
        logger.info("Discovered %d records from %s", len(records), source)
        spectra = []
        for record in records:
            try:
                raw = self.fetch(record.record_id)
                spectrum = self.normalize(raw)
                spectra.append(spectrum)
            except Exception:
                logger.exception("Failed to ingest record %s", record.record_id)
        logger.info("Ingested %d/%d spectra", len(spectra), len(records))
        return spectra
