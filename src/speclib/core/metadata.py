"""Sample metadata model for speclib.

Comprehensive sample documentation following USGS conventions,
with provenance tracking for federated ingestion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum
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
    ingested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    adapter_version: str = "0.1.0"

    # Extensible metadata bag for source-specific fields
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to a flat dictionary for HDF5 attributes.

        Returns:
            Dictionary with all metadata fields serialized as strings.
        """
        result: dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if key == "extra":
                result["extra"] = json.dumps(value) if value else "{}"
            elif isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif value is None:
                result[key] = ""
            else:
                result[key] = str(value)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SampleMetadata:
        """Deserialize metadata from a flat dictionary (HDF5 attributes).

        Args:
            data: Dictionary of metadata fields.

        Returns:
            Populated SampleMetadata instance.
        """
        kwargs: dict[str, Any] = {}

        kwargs["material_name"] = str(data.get("material_name", ""))
        kwargs["material_category"] = MaterialCategory(data["material_category"])
        kwargs["source_library"] = SourceLibrary(data["source_library"])
        kwargs["source_record_id"] = str(data.get("source_record_id", ""))
        kwargs["measurement_type"] = MeasurementType(data["measurement_type"])
        kwargs["license"] = str(data.get("license", ""))

        # Optional string fields
        for key in (
            "material_subcategory",
            "formula",
            "instrument",
            "grain_size",
            "purity",
            "description",
            "locality",
            "citation",
            "xrd_results",
            "em_results",
            "source_filename",
            "adapter_version",
        ):
            if data.get(key):
                kwargs[key] = str(data[key])

        # Date fields
        date_str = data.get("measurement_date", "")
        if date_str:
            kwargs["measurement_date"] = date.fromisoformat(str(date_str))

        ingested_str = data.get("ingested_at", "")
        if ingested_str:
            kwargs["ingested_at"] = datetime.fromisoformat(str(ingested_str))

        # Spatial fields
        for key in ("geometry_wkt", "geometry_ky_wkt"):
            val = data.get(key, "")
            kwargs[key] = str(val) if val else None

        # Extra bag
        extra_str = data.get("extra", "{}")
        if extra_str:
            kwargs["extra"] = json.loads(str(extra_str))

        return cls(**kwargs)
