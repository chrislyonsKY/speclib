"""Kentucky field data ingestion adapter for CID CI-710 spectrometer.

Parses SpectraSnap! CSV output from the CID Bio-Science CI-710
leaf spectrometer used in the Lyons et al. (2024) invasive species study.

Instrument: CID CI-710 (Ocean Optics USB4000, 3648px CCD, 400-950nm)
Software: SpectraSnap! by CID Bio-Science
"""

from __future__ import annotations

import logging
import re
from datetime import date
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

# CI-710 rated spectral range (nm)
CI710_MIN_NM = 400.0
CI710_MAX_NM = 950.0

# Filename pattern: {site}{number}_{position}{measurement}_{timestamp}.csv
_FILENAME_RE = re.compile(
    r"^(?P<site>[a-zA-Z]+)(?P<site_num>\d+)_"
    r"(?P<position>lower|mid|upper)(?P<meas_num>\d+)_"
    r"(?P<timestamp>\d+)$"
)

# Specimen ID pattern (from CSV header): {Site}{number}_{Position}{measurement}
_SPECIMEN_RE = re.compile(
    r"^(?P<site>[a-zA-Z]+)(?P<site_num>\d+)_"
    r"(?P<position>lower|mid|upper)(?P<meas_num>\d+)$",
    re.IGNORECASE,
)

# Site-to-species mapping
_SITE_SPECIES: dict[str, tuple[str, str]] = {
    "shelby": ("Amur honeysuckle", "Lonicera maackii"),
    "raven": ("Amur honeysuckle", "Lonicera maackii"),
    "bernheim": ("Callery pear", "Pyrus calleryana"),
}

# Site-to-locality mapping
_SITE_LOCALITY: dict[str, str] = {
    "shelby": "Shelby Trails, Kentucky",
    "raven": "Raven Run, Kentucky",
    "bernheim": "Bernheim Forest, Kentucky",
}

# Collection date mapping (from directory names)
_DIR_DATES: dict[str, date] = {
    "Spectrometer_Data_9_17_2020": date(2020, 9, 17),
    "Spectrometer_Data_9_19_2020": date(2020, 9, 19),
}


class KyFieldAdapter(BaseAdapter):
    """Ingestion adapter for Kentucky field spectral data (CI-710).

    Reads SpectraSnap! CSV files containing leaf-level reflectance
    measurements from invasive species field campaigns.
    """

    def discover(self) -> list[SourceRecord]:
        """List available spectra from the configured data directories.

        Returns:
            List of SourceRecord objects, one per CSV data file.
        """
        data_dirs = self.config.get("data_dirs", [])
        if not data_dirs:
            data_dir = self.config.get("data_dir")
            if data_dir:
                data_dirs = [data_dir]

        records: list[SourceRecord] = []
        for dir_str in data_dirs:
            data_path = Path(dir_str)
            if not data_path.exists():
                logger.warning("Data directory not found: %s", data_path)
                continue

            for csv_path in sorted(data_path.glob("*.csv")):
                if "_Calculations" in csv_path.name:
                    continue

                stem = csv_path.stem
                parsed = _parse_filename(stem)

                # For "untitled" files, read specimen ID from CSV header
                if parsed.get("site") == "unknown":
                    specimen_id = _read_specimen_id(csv_path)
                    if specimen_id:
                        header_parsed = _parse_specimen_id(specimen_id)
                        if header_parsed:
                            parsed = header_parsed

                site = parsed.get("site", "unknown")
                common_name, _ = _SITE_SPECIES.get(site.lower(), ("Unknown", "Unknown"))

                records.append(
                    SourceRecord(
                        record_id=str(csv_path),
                        name=stem,
                        category="KY_INVASIVE",
                        metadata={
                            "site": site,
                            "site_number": parsed.get("site_num", ""),
                            "canopy_position": parsed.get("position", ""),
                            "measurement_number": parsed.get("meas_num", ""),
                            "common_name": common_name,
                            "data_dir": data_path.name,
                        },
                    )
                )

        logger.info("Discovered %d KY field spectra", len(records))
        return records

    def fetch(self, record_id: str) -> RawSpectrum:
        """Read a single SpectraSnap! CSV file.

        Args:
            record_id: Absolute path to the CSV file.

        Returns:
            RawSpectrum with wavelengths (nm) and reflectance (%).
        """
        csv_path = Path(record_id)
        header_meta = _parse_csv_header(csv_path)

        wavelengths: list[float] = []
        reflectance_pct: list[float] = []
        raw_counts: list[float] = []

        with csv_path.open() as f:
            lines = f.readlines()

        data_start = _find_data_start(lines)
        layer_count = 0

        for line in lines[data_start:]:
            line = line.strip()
            if not line:
                continue

            # Stop at calibration/metadata sections that follow Layer 1
            if line.startswith("Peak Wavelength"):
                break
            if "Calibration" in line:
                break

            # Detect layer boundaries (new "Layer Title" header signals next layer)
            if line.startswith("Layer Title") or line.startswith("Layer "):
                if "Title" in line:
                    layer_count += 1
                    if layer_count > 1:
                        break
                continue
            if line.startswith("Mode,") or line.startswith("Wavelength,"):
                continue

            parts = line.split(",")
            if len(parts) < 3:
                continue

            try:
                wl = float(parts[0])
            except ValueError:
                continue

            # Detect second layer by wavelength decrease
            if wavelengths and wl < wavelengths[-1] - 10.0:
                break

            try:
                raw = float(parts[1])
            except ValueError:
                raw = float("nan")

            refl_str = parts[2].strip().rstrip("%")
            try:
                refl = float(refl_str)
            except ValueError:
                refl = float("nan")

            wavelengths.append(wl)
            reflectance_pct.append(refl)
            raw_counts.append(raw)

        # Read companion calculations file
        calc_path = csv_path.with_name(csv_path.stem + "_Calculations.csv")
        indices = _parse_calculations(calc_path) if calc_path.exists() else {}

        metadata = {
            **header_meta,
            "raw_counts_summary": {
                "min": float(np.nanmin(raw_counts)) if raw_counts else 0,
                "max": float(np.nanmax(raw_counts)) if raw_counts else 0,
            },
            "vegetation_indices": indices,
            "source_file": csv_path.name,
        }

        return RawSpectrum(
            record_id=record_id,
            wavelengths=np.array(wavelengths),
            reflectance=np.array(reflectance_pct),
            wavelength_unit="nm",
            reflectance_scale="percent",
            metadata=metadata,
        )

    def normalize(self, raw: RawSpectrum) -> Spectrum:
        """Convert CI-710 raw data to normalized Spectrum.

        Args:
            raw: RawSpectrum from fetch().

        Returns:
            Normalized Spectrum with wavelength in um and reflectance 0-1.
        """
        csv_path = Path(raw.record_id)
        parsed = _parse_filename(csv_path.stem)

        # For "untitled" files, use specimen ID from CSV header
        if parsed.get("site") == "unknown":
            specimen_id = raw.metadata.get("specimen_id", "")
            if specimen_id:
                header_parsed = _parse_specimen_id(specimen_id)
                if header_parsed:
                    parsed = header_parsed

        # Convert wavelength nm -> um
        wavelengths_um = raw.wavelengths / 1000.0

        # Convert reflectance % -> 0-1
        reflectance = raw.reflectance / 100.0

        # Mask values outside CI-710 rated range
        outside_range = (raw.wavelengths < CI710_MIN_NM) | (raw.wavelengths > CI710_MAX_NM)
        reflectance[outside_range] = np.nan

        # Determine species from site name
        site = parsed.get("site", "unknown").lower()
        common_name, binomial = _SITE_SPECIES.get(site, ("Unknown invasive", "Unknown"))

        # Determine collection date from parent directory
        dir_name = csv_path.parent.name
        meas_date = _DIR_DATES.get(dir_name)

        # Build name
        position = parsed.get("position", "unknown")
        site_num = parsed.get("site_num", "")
        meas_num = parsed.get("meas_num", "")
        name = f"{binomial} {site}{site_num} {position}{meas_num}"

        metadata = SampleMetadata(
            material_name=binomial,
            material_category=MaterialCategory.KY_INVASIVE,
            source_library=SourceLibrary.KY_FIELD,
            source_record_id=csv_path.stem,
            measurement_type=MeasurementType.FIELD,
            license="CC-BY-4.0",
            material_subcategory=common_name,
            instrument="CID CI-710 (Ocean Optics USB4000)",
            measurement_date=meas_date,
            description=f"Leaf reflectance, {position} canopy, site {site}{site_num}",
            locality=_SITE_LOCALITY.get(site, "Kentucky"),
            citation=(
                "Lyons, W. C., Gyawali, B. R., Cristan, R., Acharya, S.,"
                " Gebremedhin, M., & Andries, K. (2024). Evaluating spectral"
                " properties of invasive plant species in Kentucky recreation"
                " areas. International Journal of Remote Sensing, 45(18),"
                " 6470-6494. https://doi.org/10.1080/01431161.2024.2391095"
            ),
            source_filename=csv_path.name,
            extra=raw.metadata,
        )

        return Spectrum(
            name=name,
            wavelengths=wavelengths_um,
            reflectance=reflectance,
            metadata=metadata,
            quality=QualityFlag.GOOD,
        )


def _parse_filename(stem: str) -> dict[str, str]:
    """Parse a SpectraSnap! filename into components.

    Args:
        stem: Filename without extension.

    Returns:
        Dict with site, site_num, position, meas_num, timestamp keys.
    """
    match = _FILENAME_RE.match(stem)
    if match:
        return match.groupdict()
    # Handle "untitled" prefix files
    return {"site": "unknown", "site_num": "", "position": "", "meas_num": "", "timestamp": stem}


def _parse_csv_header(csv_path: Path) -> dict[str, str]:
    """Parse the SpectraSnap! CSV header for measurement settings.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        Dict with mode, integration_time, boxcar_width, scans_to_average.
    """
    result: dict[str, str] = {}
    with csv_path.open() as f:
        lines = [f.readline().strip() for _ in range(6)]

    # Line 0: "Layer Title, Color, Specimen ID"
    # Line 1: "Layer 1, Blue, shelby4_lower1"
    if len(lines) > 1:
        parts = lines[1].split(",")
        if len(parts) >= 3:
            result["specimen_id"] = parts[2].strip()

    # Line 3: "Mode, Integration Time, Boxcar Width, Scans to Average"
    # Line 4: "Reflectance,150 ms,50,1"
    if len(lines) > 4:
        parts = lines[4].split(",")
        if len(parts) >= 4:
            result["mode"] = parts[0].strip()
            result["integration_time"] = parts[1].strip()
            result["boxcar_width"] = parts[2].strip()
            result["scans_to_average"] = parts[3].strip()

    return result


def _find_data_start(lines: list[str]) -> int:
    """Find the line index where spectral data begins.

    Args:
        lines: All lines from the CSV file.

    Returns:
        Index of the first data line (after the "Wavelength,..." header).
    """
    for i, line in enumerate(lines):
        if line.strip().startswith("Wavelength,"):
            return i + 1
    return 6  # fallback


def _read_specimen_id(csv_path: Path) -> str:
    """Read the specimen ID from a SpectraSnap! CSV header.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        Specimen ID string, or empty string if not found.
    """
    with csv_path.open() as f:
        _header_line = f.readline()  # "Layer Title, Color, Specimen ID"
        data_line = f.readline().strip()
    parts = data_line.split(",")
    if len(parts) >= 3:
        return parts[2].strip()
    return ""


def _parse_specimen_id(specimen_id: str) -> dict[str, str] | None:
    """Parse a specimen ID string into site/position/number components.

    Args:
        specimen_id: Specimen ID from CSV header (e.g., "Bernheim1_Lower1").

    Returns:
        Dict with site, site_num, position, meas_num keys, or None if no match.
    """
    match = _SPECIMEN_RE.match(specimen_id)
    if match:
        groups = match.groupdict()
        # Normalize to lowercase for consistent site-species lookup
        groups["site"] = groups["site"].lower()
        groups["position"] = groups["position"].lower()
        return groups
    return None


def _parse_calculations(calc_path: Path) -> dict[str, float]:
    """Parse a SpectraSnap! Calculations CSV for vegetation indices.

    Args:
        calc_path: Path to the _Calculations.csv file.

    Returns:
        Dict mapping index name to value (e.g., {"NDVI": 0.67}).
    """
    indices: dict[str, float] = {}
    with calc_path.open() as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("Title") or line.startswith("Layer,"):
            continue
        parts = line.split(",")
        if len(parts) >= 3 and parts[0].strip().startswith("Layer"):
            name = parts[1].strip()
            try:
                value = float(parts[2].strip())
                indices[name] = value
            except ValueError:
                pass

    return indices
