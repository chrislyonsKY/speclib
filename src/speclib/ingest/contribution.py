"""Community contribution ingestion adapter.

Reads standardized contribution format: a contribution.yaml manifest
plus CSV data files with wavelength_um/reflectance columns.

All contributions must be calibrated reflectance data with
verified institutional affiliation.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import numpy as np
import yaml

from speclib.core.metadata import SampleMetadata
from speclib.core.spectrum import (
    MaterialCategory,
    MeasurementType,
    QualityFlag,
    SourceLibrary,
    Spectrum,
)
from speclib.ingest.base import BaseAdapter, RawSpectrum, SourceRecord

logger = logging.getLogger(__name__)

REQUIRED_MANIFEST_FIELDS = {
    "contributor.name",
    "contributor.affiliation",
    "contributor.email",
    "license",
    "instrument",
    "measurement_type",
    "calibrated",
    "calibration_method",
    "material_category",
}


class ContributionAdapter(BaseAdapter):
    """Ingestion adapter for community-contributed spectral data.

    Reads a contribution.yaml manifest and associated CSV files
    from a contribution directory. Enforces calibration requirements
    and institutional affiliation.
    """

    def __init__(self, config_path: Path) -> None:
        """Initialize with path to the contribution.yaml manifest.

        Args:
            config_path: Path to contribution.yaml.
        """
        self.config_path = Path(config_path)
        with self.config_path.open() as f:
            self.config = yaml.safe_load(f)
        self.contribution_dir = self.config_path.parent
        self._validate_manifest()

    def _validate_manifest(self) -> None:
        """Validate that the manifest has all required fields.

        Raises:
            ValueError: If required fields are missing or calibrated is not True.
        """
        missing = []
        contributor = self.config.get("contributor", {})
        for field in REQUIRED_MANIFEST_FIELDS:
            parts = field.split(".")
            if len(parts) == 2:
                val = contributor.get(parts[1], "")
            else:
                val = self.config.get(parts[0], "")
            if not val:
                missing.append(field)

        if missing:
            msg = f"Missing required fields in contribution.yaml: {', '.join(missing)}"
            raise ValueError(msg)

        if not self.config.get("calibrated"):
            msg = "Contributions must have calibrated: true"
            raise ValueError(msg)

    def discover(self) -> list[SourceRecord]:
        """List spectra defined in the contribution manifest.

        Returns:
            List of SourceRecord objects, one per spectrum entry.
        """
        spectra_entries = self.config.get("spectra", [])
        records: list[SourceRecord] = []

        for entry in spectra_entries:
            csv_file = entry.get("file", "")
            csv_path = self.contribution_dir / csv_file
            if not csv_path.exists():
                logger.warning("CSV file not found: %s", csv_path)
                continue

            records.append(
                SourceRecord(
                    record_id=str(csv_path),
                    name=entry.get("name", csv_path.stem),
                    category=self.config.get("material_category", "MINERAL"),
                    metadata=entry,
                )
            )

        logger.info("Discovered %d contributed spectra", len(records))
        return records

    def fetch(self, record_id: str) -> RawSpectrum:
        """Read a contribution CSV file.

        Expected columns: wavelength_um, reflectance, [error]

        Args:
            record_id: Absolute path to the CSV file.

        Returns:
            RawSpectrum with wavelengths (um) and reflectance (0-1).
        """
        csv_path = Path(record_id)
        wavelengths: list[float] = []
        reflectance: list[float] = []
        errors: list[float] = []

        with csv_path.open() as f:
            header = f.readline().strip().lower()
            has_error = "error" in header

            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                try:
                    wl = float(parts[0])
                    refl = float(parts[1])
                    wavelengths.append(wl)
                    reflectance.append(refl)
                    if has_error and len(parts) >= 3:
                        errors.append(float(parts[2]))
                except ValueError:
                    continue

        metadata = {
            "source_file": csv_path.name,
            "has_errors": bool(errors),
        }

        return RawSpectrum(
            record_id=record_id,
            wavelengths=np.array(wavelengths),
            reflectance=np.array(reflectance),
            wavelength_unit="um",
            reflectance_scale="fractional",
            metadata={
                **metadata,
                "errors": np.array(errors) if errors else None,
            },
        )

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert contributed data to normalized Spectrum.

        Args:
            raw: RawSpectrum from fetch().

        Returns:
            Normalized Spectrum with COMMUNITY quality tier.
        """
        csv_path = Path(raw.record_id)

        # Find the matching entry in the manifest
        entry_meta = {}
        for entry in self.config.get("spectra", []):
            if entry.get("file") == csv_path.name:
                entry_meta = entry
                break

        contributor = self.config.get("contributor", {})
        category_str = self.config.get("material_category", "MINERAL")
        meas_type_str = self.config.get("measurement_type", "FIELD")

        meas_date = None
        date_str = entry_meta.get("measurement_date", "")
        if date_str:
            meas_date = date.fromisoformat(str(date_str))

        errors = raw.metadata.get("errors")

        metadata = SampleMetadata(
            material_name=entry_meta.get("material_name", csv_path.stem),
            material_category=MaterialCategory(category_str),
            source_library=SourceLibrary.CUSTOM,
            source_record_id=csv_path.stem,
            measurement_type=MeasurementType(meas_type_str),
            license=self.config.get("license", ""),
            instrument=self.config.get("instrument", ""),
            measurement_date=meas_date,
            description=entry_meta.get("description", ""),
            locality=entry_meta.get("locality", ""),
            citation=self.config.get("citation", ""),
            source_filename=csv_path.name,
            extra={
                "contributor_name": contributor.get("name", ""),
                "contributor_affiliation": contributor.get("affiliation", ""),
                "contributor_email": contributor.get("email", ""),
                "calibration_method": self.config.get("calibration_method", ""),
                "quality_tier": "COMMUNITY",
            },
        )

        name = entry_meta.get("name", csv_path.stem)

        return Spectrum(
            name=name,
            wavelengths=raw.wavelengths,
            reflectance=raw.reflectance,
            metadata=metadata,
            quality=QualityFlag.GOOD,
            errors=errors if isinstance(errors, np.ndarray) else None,
        )
