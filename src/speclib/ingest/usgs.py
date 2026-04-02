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


class UsgsAdapter(BaseAdapter):
    """Ingestion adapter for the USGS Spectral Library v7 (splib07a).

    Reads ASCII data files with separate wavelength files. Handles
    the USGS delete value convention and chapter-based organization.
    """

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

        chapter_map = self.config.get("chapter_map", {})
        records: list[SourceRecord] = []

        for txt_path in sorted(data_path.rglob("*.txt")):
            if txt_path.name.startswith("splib07a_Wavelengths"):
                continue

            stem = txt_path.stem
            chapter = _extract_chapter(stem, txt_path)
            category = chapter_map.get(chapter, "MINERAL")

            records.append(
                SourceRecord(
                    record_id=str(txt_path),
                    name=stem,
                    category=category,
                    metadata={
                        "chapter": chapter,
                        "relative_path": str(txt_path.relative_to(data_path)),
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
        wavelength_path = _find_wavelength_file(refl_path)

        wavelengths = _read_usgs_column(wavelength_path)
        reflectance = _read_usgs_column(refl_path)

        # Truncate to shorter array if lengths differ
        min_len = min(len(wavelengths), len(reflectance))
        wavelengths = wavelengths[:min_len]
        reflectance = reflectance[:min_len]

        # Replace USGS delete values with NaN
        delete_mask = np.isclose(reflectance, USGS_DELETE_VALUE, rtol=1e-3)
        reflectance[delete_mask] = np.nan

        wl_delete = np.isclose(wavelengths, USGS_DELETE_VALUE, rtol=1e-3)
        wavelengths[wl_delete] = np.nan

        return RawSpectrum(
            record_id=record_id,
            wavelengths=wavelengths,
            reflectance=reflectance,
            wavelength_unit="um",
            reflectance_scale="fractional",
            metadata={"source_file": refl_path.name},
        )

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert USGS raw data to normalized Spectrum.

        Args:
            raw: RawSpectrum from fetch().

        Returns:
            Normalized Spectrum (already in um/0-1).
        """
        refl_path = Path(raw.record_id)
        chapter = _extract_chapter(refl_path.stem, refl_path)
        chapter_map = self.config.get("chapter_map", {})
        category_str = chapter_map.get(chapter, "MINERAL")
        category = MaterialCategory(category_str)

        metadata = SampleMetadata(
            material_name=refl_path.stem,
            material_category=category,
            source_library=SourceLibrary.USGS_SPLIB07,
            source_record_id=refl_path.stem,
            measurement_type=MeasurementType.LABORATORY,
            license=self.config.get("license", "US Public Domain"),
            citation=self.config.get("citation", ""),
            source_filename=refl_path.name,
        )

        return Spectrum(
            name=refl_path.stem,
            wavelengths=raw.wavelengths,
            reflectance=raw.reflectance,
            metadata=metadata,
            quality=QualityFlag.GOOD,
        )


def _read_usgs_column(path: Path) -> np.ndarray:
    """Read a single-column USGS ASCII data file.

    Skips header lines that don't parse as floats.

    Args:
        path: Path to the data file.

    Returns:
        1D numpy array of values.
    """
    values: list[float] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                values.append(float(line))
            except ValueError:
                continue
    return np.array(values, dtype=np.float64)


def _find_wavelength_file(refl_path: Path) -> Path:
    """Locate the wavelength file for a given reflectance file.

    USGS convention: wavelength files are in a parent directory or
    sibling directory named with 'Wavelengths'.

    Args:
        refl_path: Path to the reflectance data file.

    Returns:
        Path to the matching wavelength file.

    Raises:
        FileNotFoundError: If no wavelength file is found.
    """
    # Search in same directory and parent directories
    for search_dir in [refl_path.parent, refl_path.parent.parent, refl_path.parent.parent.parent]:
        for wl_file in search_dir.glob("*Wavelengths*.txt"):
            return wl_file

    msg = f"No wavelength file found for {refl_path}"
    raise FileNotFoundError(msg)


def _extract_chapter(stem: str, path: Path) -> str:
    """Extract the USGS chapter code from a filename or path.

    Args:
        stem: Filename without extension.
        path: Full file path.

    Returns:
        Chapter string like 'Ch01', or empty string if not found.
    """
    # Try filename pattern
    match = re.search(r"Ch(\d{2})", stem)
    if match:
        return f"Ch{match.group(1)}"

    # Try parent directory names
    for part in path.parts:
        match = re.search(r"Ch(\d{2})", part)
        if match:
            return f"Ch{match.group(1)}"

    return ""
