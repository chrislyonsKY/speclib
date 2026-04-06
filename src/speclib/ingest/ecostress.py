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
    "non photosynthetic vegetation": "NONPHOTOSYNTHETIC_VEGETATION",
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

        with txt_path.open(encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Find data start: first line after a blank line that follows header
        data_start = 0
        in_header = True
        for i, line in enumerate(lines):
            if in_header:
                if not line.strip():
                    in_header = False
            else:
                data_start = i
                break

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

        wl_unit = header.get("X Units", "").lower()
        data_unit = header.get("Y Units", "").lower()

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

        # Sort ascending if wavelengths are descending
        if len(wavelengths) > 1 and wavelengths[0] > wavelengths[-1]:
            sort_idx = np.argsort(wavelengths)
            wavelengths = wavelengths[sort_idx]
            reflectance = reflectance[sort_idx]

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
            source_record_id=header.get("Sample No.", Path(raw.record_id).stem),
            measurement_type=MeasurementType.LABORATORY,
            license=self.config.get("license", "CC0 / Public Domain"),
            material_subcategory=header.get("Subclass", header.get("Class", "")),
            formula=header.get("Class", ""),
            instrument=header.get("Measurement", ""),
            description=header.get("Description", ""),
            locality=header.get("Origin", ""),
            citation=self.config.get("citation", ""),
            source_filename=Path(raw.record_id).name,
        )

        # Store genus/species in extra if present
        extra: dict[str, str] = {}
        if header.get("Genus"):
            extra["genus"] = header["Genus"]
        if header.get("Species"):
            extra["species"] = header["Species"]
        if header.get("Particle Size"):
            extra["particle_size"] = header["Particle Size"]
        if header.get("Wavelength Range"):
            extra["wavelength_range"] = header["Wavelength Range"]
        if header.get("Owner"):
            extra["owner"] = header["Owner"]
        if header.get("Collection Date"):
            extra["collection_date"] = header["Collection Date"]

        # Link paired ancillary file if it exists
        ancillary_name = Path(raw.record_id).name.replace(".spectrum.txt", ".ancillary.txt")
        ancillary_file = Path(raw.record_id).parent / ancillary_name
        if ancillary_file.exists():
            try:
                anc_data = _read_ancillary(ancillary_file)
                if "ancillary_text" in anc_data:
                    extra["ancillary_text"] = anc_data["ancillary_text"]
                if anc_data.get("Chemistry"):
                    extra["chemistry"] = anc_data["Chemistry"]
                if anc_data.get("Biophysical Properties"):
                    extra["biophysical_properties"] = anc_data["Biophysical Properties"]
                if anc_data.get("Reference"):
                    citation = self.config.get("citation", "")
                    ref = anc_data["Reference"]
                    metadata.citation = f"{citation}; {ref}" if citation else ref
            except Exception:
                logger.warning("Failed to read ancillary file: %s", ancillary_file)

        if extra:
            metadata.extra = extra

        return Spectrum(
            name=name,
            wavelengths=wavelengths,
            reflectance=reflectance,
            metadata=metadata,
            quality=QualityFlag.GOOD,
        )


def _read_ancillary(path: Path) -> dict[str, str]:
    """Read an ECOSTRESS/ASTER ancillary metadata file.

    Ancillary files have the same key-value header as spectrum files,
    followed by freeform text containing chemistry, XRD analysis, etc.

    Args:
        path: Path to the .ancillary.txt file.

    Returns:
        Dictionary with parsed header fields plus 'ancillary_text'
        containing any freeform content below the header.
    """
    result = _read_header(path)

    with path.open(encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    # Find where header ends (first blank line)
    body_start = 0
    for i, line in enumerate(all_lines):
        if not line.strip():
            body_start = i + 1
            break

    freeform = "".join(all_lines[body_start:]).strip()
    if freeform:
        result["ancillary_text"] = freeform

    return result


def _read_header(path: Path) -> dict[str, str]:
    """Read the structured header from an ECOSTRESS/ASTER spectrum file.

    Parses key-value pairs separated by the first colon on each line.
    Header ends at the blank line following the last header field.

    Args:
        path: Path to the .spectrum.txt or .ancillary.txt file.

    Returns:
        Dictionary mapping header field names to their values.
    """
    header: dict[str, str] = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                break
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                header[key.strip()] = value.strip()
            else:
                if header:
                    break
    return header
