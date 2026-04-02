"""USGS Spectral Library v7 (splib07a) ingestion adapter.

Parses ASCII text files from the USGS Spectral Library Version 7.
Wavelength and reflectance data are in separate files. Delete values
(-1.23e+34) are converted to NaN.

Reference: Kokaly et al. (2017), USGS Data Series 1035.
"""

from __future__ import annotations

import logging
import re
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

USGS_DELETE_VALUE = -1.23e34

# Spectrometer code mapping: filename substring → wavelength file keyword
_SPECTROMETER_MAP = {
    "ASDFR": "ASD",
    "ASDHR": "ASD",
    "ASDNG": "ASD",
    "ASDFRb": "ASD",
    "ASDHRb": "ASD",
    "ASDNGb": "ASD",
    "BECK": "BECK",
    "BECKa": "BECK",
    "BECKb": "BECK",
    "NIC4": "NIC4",
    "NIC4bbb": "NIC4",
    "AVIRIS": "AVIRIS",
}

# Chapter directory name → MaterialCategory value
_CHAPTER_DIR_MAP = {
    "ChapterM_Minerals": "MINERAL",
    "ChapterS_SoilsAndMixtures": "SOIL",
    "ChapterC_Coatings": "MIXTURE",
    "ChapterL_Liquids": "WATER",
    "ChapterO_OrganicCompounds": "ORGANIC",
    "ChapterA_ArtificialMaterials": "MANMADE",
    "ChapterV_Vegetation": "VEGETATION",
}


class UsgsAdapter(BaseAdapter):
    """Ingestion adapter for the USGS Spectral Library v7 (splib07a).

    Reads ASCII data files with separate wavelength files. Handles
    the USGS delete value convention and chapter-based organization.
    """

    def __init__(self, config_path: Path) -> None:
        """Initialize and cache wavelength files.

        Args:
            config_path: Path to YAML config.
        """
        super().__init__(config_path)
        self._wavelength_cache: dict[str, np.ndarray] = {}

    def discover(self) -> list[SourceRecord]:
        """List available spectra from the ASCII data directory.

        Returns:
            List of SourceRecord objects.
        """
        ascii_dir = self.config.get("ascii_data_dir")
        if not ascii_dir:
            logger.warning("ascii_data_dir not configured")
            return []

        data_path = Path(ascii_dir)
        if not data_path.exists():
            logger.warning("ASCII data directory not found: %s", data_path)
            return []

        records: list[SourceRecord] = []

        for chapter_dir in sorted(data_path.iterdir()):
            if not chapter_dir.is_dir() or chapter_dir.name.startswith("error"):
                continue

            category = _CHAPTER_DIR_MAP.get(chapter_dir.name, "MINERAL")

            for txt_path in sorted(chapter_dir.glob("*.txt")):
                stem = txt_path.stem
                records.append(
                    SourceRecord(
                        record_id=str(txt_path),
                        name=_parse_spectrum_name(stem),
                        category=category,
                        metadata={
                            "chapter_dir": chapter_dir.name,
                            "filename": txt_path.name,
                        },
                    )
                )

        logger.info("Discovered %d USGS spectra", len(records))
        return records

    def fetch(self, record_id: str) -> RawSpectrum:
        """Read a USGS ASCII spectrum file and its wavelength file.

        Args:
            record_id: Absolute path to the reflectance file.

        Returns:
            RawSpectrum with wavelengths (um) and reflectance (0-1).
        """
        refl_path = Path(record_id)

        # Read reflectance (skip header line)
        reflectance = _read_usgs_data(refl_path)

        # Find and read matching wavelength file
        spectrometer = _extract_spectrometer(refl_path.stem)
        wavelengths = self._get_wavelengths(refl_path, spectrometer)

        # Truncate to shorter array
        min_len = min(len(wavelengths), len(reflectance))
        wavelengths = wavelengths[:min_len]
        reflectance = reflectance[:min_len]

        # Replace USGS delete values with NaN
        delete_mask = np.abs(reflectance) > 1.0e30
        reflectance[delete_mask] = np.nan

        wl_delete = np.abs(wavelengths) > 1.0e30
        wavelengths[wl_delete] = np.nan

        # Parse header for record info
        header = _read_header(refl_path)

        return RawSpectrum(
            record_id=record_id,
            wavelengths=wavelengths,
            reflectance=reflectance,
            wavelength_unit="um",
            reflectance_scale="fractional",
            metadata={
                "source_file": refl_path.name,
                "header": header,
                "spectrometer": spectrometer,
            },
        )

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert USGS raw data to normalized Spectrum.

        Args:
            raw: RawSpectrum from fetch().

        Returns:
            Normalized Spectrum (already in um/0-1).
        """
        refl_path = Path(raw.record_id)
        chapter_dir = refl_path.parent.name
        category_str = _CHAPTER_DIR_MAP.get(chapter_dir, "MINERAL")
        category = MaterialCategory(category_str)

        name = _parse_spectrum_name(refl_path.stem)
        header = raw.metadata.get("header", "")

        metadata = SampleMetadata(
            material_name=name,
            material_category=category,
            source_library=SourceLibrary.USGS_SPLIB07,
            source_record_id=refl_path.stem,
            measurement_type=MeasurementType.LABORATORY,
            license=self.config.get("license", "US Public Domain"),
            instrument=raw.metadata.get("spectrometer", ""),
            citation=self.config.get("citation", ""),
            description=header,
            source_filename=refl_path.name,
        )

        return Spectrum(
            name=name,
            wavelengths=raw.wavelengths,
            reflectance=raw.reflectance,
            metadata=metadata,
            quality=QualityFlag.GOOD,
        )

    def _get_wavelengths(self, refl_path: Path, spectrometer: str) -> np.ndarray:
        """Get cached wavelength array for a spectrometer type.

        Args:
            refl_path: Path to the reflectance file (for locating wavelength files).
            spectrometer: Spectrometer keyword (ASD, BECK, NIC4, AVIRIS).

        Returns:
            Wavelength array in micrometers.
        """
        if spectrometer in self._wavelength_cache:
            return self._wavelength_cache[spectrometer].copy()

        wl_file = _find_wavelength_file(refl_path, spectrometer)
        wavelengths = _read_usgs_data(wl_file)
        self._wavelength_cache[spectrometer] = wavelengths
        logger.info(
            "Cached %d wavelengths for %s from %s",
            len(wavelengths),
            spectrometer,
            wl_file.name,
        )
        return wavelengths.copy()


def _read_usgs_data(path: Path) -> np.ndarray:
    """Read a USGS ASCII data file, skipping the header line.

    Args:
        path: Path to the data file.

    Returns:
        1D numpy array of values.
    """
    values: list[float] = []
    with path.open() as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            # Skip header line (contains non-numeric text)
            if i == 0 and not _is_numeric(line):
                continue
            try:
                values.append(float(line))
            except ValueError:
                continue
    return np.array(values, dtype=np.float64)


def _read_header(path: Path) -> str:
    """Read the first line of a USGS file as the header/title.

    Args:
        path: Path to the data file.

    Returns:
        Header string.
    """
    with path.open() as f:
        return f.readline().strip()


def _is_numeric(s: str) -> bool:
    """Check if a string is a numeric value."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _find_wavelength_file(refl_path: Path, spectrometer: str) -> Path:
    """Locate the wavelength file matching a spectrometer type.

    Args:
        refl_path: Path to the reflectance data file.
        spectrometer: Spectrometer keyword (ASD, BECK, NIC4, AVIRIS).

    Returns:
        Path to the matching wavelength file.

    Raises:
        FileNotFoundError: If no wavelength file is found.
    """
    # Wavelength files are in the parent of the chapter directories
    for search_dir in [
        refl_path.parent.parent,
        refl_path.parent,
        refl_path.parent.parent.parent,
    ]:
        if not search_dir.exists():
            continue
        for wl_file in search_dir.glob("*Wavelengths*.txt"):
            if spectrometer in wl_file.name:
                return wl_file

    # Fallback: any wavelength file
    for search_dir in [refl_path.parent.parent, refl_path.parent]:
        if not search_dir.exists():
            continue
        for wl_file in search_dir.glob("*Wavelengths*.txt"):
            return wl_file

    msg = f"No wavelength file found for {refl_path} (spectrometer: {spectrometer})"
    raise FileNotFoundError(msg)


def _extract_spectrometer(stem: str) -> str:
    """Extract the spectrometer type from a USGS filename.

    Args:
        stem: Filename without extension.

    Returns:
        Spectrometer keyword (ASD, BECK, NIC4, AVIRIS).
    """
    # Try known codes from longest to shortest
    for code, keyword in sorted(_SPECTROMETER_MAP.items(), key=lambda x: -len(x[0])):
        if code in stem:
            return keyword
    return "ASD"  # default


def _parse_spectrum_name(stem: str) -> str:
    """Parse a human-readable name from a USGS filename.

    Converts 'splib07a_Acmite_NMNH133746_Pyroxene_BECKa_AREF'
    to 'Acmite NMNH133746 Pyroxene'.

    Args:
        stem: Filename without extension.

    Returns:
        Cleaned spectrum name.
    """
    # Remove prefix
    name = re.sub(r"^splib07[ab]_", "", stem)
    # Remove spectrometer and reference type suffixes
    name = re.sub(r"_(ASDFR|ASDHR|ASDNG|BECK|NIC4|AVIRIS)\w*$", "", name)
    name = re.sub(r"_(AREF|RREF)$", "", name)
    return name.replace("_", " ")
