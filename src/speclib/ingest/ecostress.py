"""ECOSTRESS / ASTER spectral library ingestion adapter.

Parses .spectrum.txt files from the ECOSTRESS and ASTER/JPL spectral
libraries. Both share nearly identical formats: a 20-line structured
header followed by wavelength/value data pairs.

Reference: Meerdink et al. (2019), Remote Sensing of Environment.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

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

# Header field names in ECOSTRESS/ASTER spectrum files
_HEADER_FIELDS = [
    "Name",
    "Type",
    "Class",
    "SubClass",
    "ParticleSize",
    "Genus",
    "Species",
    "SampleNo",
    "Owner",
    "WavelengthRange",
    "Origin",
    "CollectionDate",
    "Description",
    "Measurement",
    "FirstColumn",
    "SecondColumn",
    "WavelengthUnit",
    "DataUnit",
    "FirstXValue",
    "LastXValue",
    "NumberOfXValues",
    "AdditionalInformation",
]

# Mapping from ECOSTRESS Type field to MaterialCategory
_TYPE_MAP: dict[str, str] = {
    "mineral": "MINERAL",
    "rock": "ROCK",
    "soil": "SOIL",
    "vegetation": "VEGETATION",
    "water": "WATER",
    "manmade": "MANMADE",
    "mixture": "MIXTURE",
    "organic": "ORGANIC",
}


class EcostressAdapter(BaseAdapter):
    """Ingestion adapter for the ECOSTRESS/ASTER spectral library.

    Handles .spectrum.txt files with structured 20-line headers.
    Automatically detects and converts reflectance units (fractional
    vs percentage) based on header metadata.
    """

    def discover(self) -> list[SourceRecord]:
        """List available spectra from the data directory.

        Returns:
            List of SourceRecord objects.
        """
        data_dir = self.config.get("data_dir")
        if not data_dir:
            logger.warning("data_dir not configured for %s", self.config.get("source", "ECOSTRESS"))
            return []

        data_path = Path(data_dir)
        if not data_path.exists():
            logger.warning("Data directory not found: %s", data_path)
            return []

        records: list[SourceRecord] = []
        for txt_path in sorted(data_path.rglob("*.spectrum.txt")):
            header = _read_header(txt_path)
            name = header.get("Name", txt_path.stem)
            type_str = header.get("Type", "").lower()
            category = _TYPE_MAP.get(type_str, "MINERAL")

            records.append(
                SourceRecord(
                    record_id=str(txt_path),
                    name=name,
                    category=category,
                    metadata=header,
                )
            )

        logger.info("Discovered %d ECOSTRESS/ASTER spectra", len(records))
        return records

    def fetch(self, record_id: str) -> RawSpectrum:
        """Read a single .spectrum.txt file.

        Args:
            record_id: Absolute path to the spectrum file.

        Returns:
            RawSpectrum with wavelengths and reflectance in source units.
        """
        txt_path = Path(record_id)
        header = _read_header(txt_path)

        wavelengths: list[float] = []
        values: list[float] = []

        with txt_path.open() as f:
            lines = f.readlines()

        # Data starts after the header (first ~20 lines)
        data_start = min(len(_HEADER_FIELDS), len(lines))
        for line in lines[data_start:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                parts = line.split(",")
            if len(parts) < 2:
                continue
            try:
                wl = float(parts[0])
                val = float(parts[1])
                wavelengths.append(wl)
                values.append(val)
            except ValueError:
                continue

        wl_unit = header.get("WavelengthUnit", "micrometer").lower()
        data_unit = header.get("DataUnit", "").lower()

        refl_scale = "percent" if "percent" in data_unit else "fractional"

        return RawSpectrum(
            record_id=record_id,
            wavelengths=np.array(wavelengths),
            reflectance=np.array(values),
            wavelength_unit="um" if "micro" in wl_unit else wl_unit,
            reflectance_scale=refl_scale,
            metadata=header,
        )

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert ECOSTRESS/ASTER raw data to normalized Spectrum.

        Args:
            raw: RawSpectrum from fetch().

        Returns:
            Normalized Spectrum with wavelength in um and reflectance 0-1.
        """
        wavelengths = raw.wavelengths.copy()
        reflectance = raw.reflectance.copy()

        # Convert nm to um if needed
        if raw.wavelength_unit == "nm" or (len(wavelengths) > 0 and wavelengths[0] > 100):
            wavelengths = wavelengths / 1000.0

        # Convert percentage to fractional
        if raw.reflectance_scale == "percent":
            reflectance = reflectance / 100.0

        header = raw.metadata
        source = self.config.get("source", "ECOSTRESS")
        source_lib = SourceLibrary.ECOSTRESS if source == "ECOSTRESS" else SourceLibrary.ASTER_JPL

        type_str = header.get("Type", "").lower()
        category_str = _TYPE_MAP.get(type_str, "MINERAL")
        category = MaterialCategory(category_str)

        name = header.get("Name", Path(raw.record_id).stem)

        metadata = SampleMetadata(
            material_name=name,
            material_category=category,
            source_library=source_lib,
            source_record_id=Path(raw.record_id).stem,
            measurement_type=MeasurementType.LABORATORY,
            license=self.config.get("license", "CC0 / Public Domain"),
            material_subcategory=header.get("SubClass", ""),
            formula=header.get("Class", ""),
            instrument=header.get("Measurement", ""),
            description=header.get("Description", ""),
            locality=header.get("Origin", ""),
            citation=self.config.get("citation", ""),
            source_filename=Path(raw.record_id).name,
        )

        return Spectrum(
            name=name,
            wavelengths=wavelengths,
            reflectance=reflectance,
            metadata=metadata,
            quality=QualityFlag.GOOD,
        )


def _read_header(path: Path) -> dict[str, str]:
    """Read the structured header from an ECOSTRESS/ASTER spectrum file.

    Args:
        path: Path to the .spectrum.txt file.

    Returns:
        Dictionary mapping header field names to values.
    """
    header: dict[str, str] = {}
    with path.open() as f:
        for i, line in enumerate(f):
            if i >= len(_HEADER_FIELDS):
                break
            value = line.strip()
            header[_HEADER_FIELDS[i]] = value
    return header
