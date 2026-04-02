"""Core Spectrum data class for speclib.

The fundamental data unit: a single spectral measurement with metadata,
quality flags, and provenance tracking.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

    from speclib.core.metadata import SampleMetadata


class QualityFlag(Enum):
    """Spectrum quality assessment following USGS purity conventions."""

    VERIFIED = "VERIFIED"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    SUSPECT = "SUSPECT"
    DERIVED = "DERIVED"


class MaterialCategory(Enum):
    """Top-level material classification."""

    MINERAL = "MINERAL"
    ROCK = "ROCK"
    SOIL = "SOIL"
    VEGETATION = "VEGETATION"
    VEGETATION_PLOT = "VEGETATION_PLOT"
    WATER = "WATER"
    MANMADE = "MANMADE"
    MIXTURE = "MIXTURE"
    ORGANIC = "ORGANIC"
    VOLATILE = "VOLATILE"
    KY_INVASIVE = "KY_INVASIVE"
    KY_MINERAL = "KY_MINERAL"
    KY_RECLAMATION = "KY_RECLAMATION"


class SourceLibrary(Enum):
    """Upstream spectral library identifiers."""

    USGS_SPLIB07 = "USGS_SPLIB07"
    ECOSTRESS = "ECOSTRESS"
    ASTER_JPL = "ASTER_JPL"
    EMIT_L2B = "EMIT_L2B"
    KY_FIELD = "KY_FIELD"
    CUSTOM = "CUSTOM"


class MeasurementType(Enum):
    """How the spectrum was acquired."""

    LABORATORY = "LABORATORY"
    FIELD = "FIELD"
    AIRBORNE = "AIRBORNE"
    SPACEBORNE = "SPACEBORNE"
    COMPUTED = "COMPUTED"


@dataclass
class Spectrum:
    """A single spectral measurement with metadata and quality assessment.

    Attributes:
        name: Human-readable spectrum name.
        wavelengths: Wavelength positions in micrometers (µm), sorted ascending.
        reflectance: Reflectance values on 0.0–1.0 scale.
        metadata: Full sample description and provenance.
        quality: Overall quality assessment flag.
        errors: Per-band measurement uncertainty (optional).
        spectrum_id: Unique identifier, auto-generated if not provided.
    """

    name: str
    wavelengths: np.ndarray
    reflectance: np.ndarray
    metadata: SampleMetadata
    quality: QualityFlag = QualityFlag.GOOD
    errors: np.ndarray | None = None
    spectrum_id: str = ""

    def __post_init__(self) -> None:
        """Validate spectral data integrity and generate ID if needed."""
        # TODO: Validate wavelengths sorted ascending
        # TODO: Validate wavelengths and reflectance same length
        # TODO: Validate reflectance values, flag out-of-range (don't clip)
        # TODO: Validate errors array shape if present
        # TODO: Generate spectrum_id if empty
        pass

    @property
    def n_bands(self) -> int:
        """Number of spectral channels."""
        return len(self.wavelengths)

    @property
    def wavelength_range(self) -> tuple[float, float]:
        """Wavelength coverage as (min, max) in µm."""
        return float(self.wavelengths[0]), float(self.wavelengths[-1])

    def plot(self, ax=None, **kwargs) -> None:
        """Plot this spectrum using matplotlib.

        Args:
            ax: Optional matplotlib Axes. Creates new figure if None.
            **kwargs: Passed to matplotlib plot().
        """
        # TODO: Implement matplotlib spectral plot
        # TODO: Label axes (Wavelength µm, Reflectance)
        # TODO: Include spectrum name in title/legend
        pass

    def resample(self, sensor: str | Path) -> Spectrum:
        """Resample this spectrum to a target sensor's spectral response.

        Args:
            sensor: Sensor name (e.g., 'L8_OLI') or path to custom RSR YAML.

        Returns:
            New Spectrum resampled to the target sensor bands.
        """
        # TODO: Load sensor response function
        # TODO: Oversample via cubic spline (splib07b method)
        # TODO: Convolve with Gaussian response functions
        # TODO: Return new Spectrum with effective wavelengths
        raise NotImplementedError

    def export(self, path: str | Path, format: str = "json") -> None:
        """Export this spectrum to the specified format.

        Args:
            path: Output file path.
            format: One of 'json', 'ascii', 'esl', 'sli', 'specpr'.
        """
        # TODO: Dispatch to appropriate exporter
        raise NotImplementedError

    @staticmethod
    def _generate_id(source: str, category: str, name: str) -> str:
        """Generate a deterministic spectrum ID.

        Args:
            source: Source library identifier.
            category: Material category.
            name: Spectrum name.

        Returns:
            ID in format {source}_{category}_{name_slug}_{hash8}.
        """
        slug = name.lower().replace(" ", "_")[:40]
        hash_input = f"{source}:{category}:{name}"
        hash8 = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"{source.lower()}_{category.lower()}_{slug}_{hash8}"
