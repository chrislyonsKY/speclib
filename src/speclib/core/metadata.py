"""Sample metadata model for speclib.

Comprehensive sample documentation following USGS conventions,
with provenance tracking for federated ingestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from speclib.core.spectrum import MaterialCategory, MeasurementType, SourceLibrary


@dataclass
class SampleMetadata:
    """Full sample description and provenance for a spectrum.

    Attributes:
        material_name: Canonical material name.
        material_category: Top-level classification.
        source_library: Which upstream library this came from.
        source_record_id: Original record ID in source library.
        measurement_type: How the measurement was acquired.
        license: Data license string.
    """

    # Required fields
    material_name: str
    material_category: MaterialCategory
    source_library: SourceLibrary
    source_record_id: str
    measurement_type: MeasurementType
    license: str

    # Optional descriptive fields
    material_subcategory: str = ""
    formula: str = ""
    instrument: str = ""
    measurement_date: date | None = None
    grain_size: str = ""
    purity: str = ""
    description: str = ""
    locality: str = ""
    citation: str = ""

    # Analytical results
    xrd_results: str = ""
    em_results: str = ""

    # Source file tracking
    source_filename: str = ""

    # Spatial (WKT or None)
    geometry_wkt: str | None = None  # WGS84 EPSG:4326
    geometry_ky_wkt: str | None = None  # EPSG:3089

    # Auto-populated by ingestion
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    adapter_version: str = "0.1.0"

    # Extensible metadata bag for source-specific fields
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to a flat dictionary for HDF5 attributes.

        Returns:
            Dictionary with all metadata fields serialized as strings.
        """
        # TODO: Implement serialization
        # TODO: Handle None values (store as empty string for HDF5 compat)
        # TODO: Handle date/datetime as ISO 8601 strings
        # TODO: Handle enums as their .value strings
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SampleMetadata:
        """Deserialize metadata from a flat dictionary (HDF5 attributes).

        Args:
            data: Dictionary of metadata fields.

        Returns:
            Populated SampleMetadata instance.
        """
        # TODO: Implement deserialization
        # TODO: Parse date strings back to date objects
        # TODO: Parse enum value strings back to enum instances
        raise NotImplementedError
