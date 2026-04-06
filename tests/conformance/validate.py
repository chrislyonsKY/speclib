"""Format spec validator for speclib archives.

Validates HDF5, Parquet, and JSON outputs against the format spec.
Returns a list of error strings (empty = conformant).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import h5py
import numpy as np
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

REQUIRED_ATTRS = [
    "name",
    "spectrum_id",
    "quality",
    "material_name",
    "material_category",
    "source_library",
    "source_record_id",
    "measurement_type",
    "license",
    "ingested_at",
    "adapter_version",
    "source_filename",
]

VALID_QUALITY = {"VERIFIED", "GOOD", "FAIR", "POOR", "SUSPECT", "DERIVED"}

VALID_CATEGORY = {
    "MINERAL",
    "ROCK",
    "SOIL",
    "VEGETATION",
    "VEGETATION_PLOT",
    "WATER",
    "MANMADE",
    "MIXTURE",
    "ORGANIC",
    "NONPHOTOSYNTHETIC_VEGETATION",
    "VOLATILE",
    "KY_INVASIVE",
    "KY_MINERAL",
    "KY_RECLAMATION",
}

VALID_SOURCE = {
    "USGS_SPLIB07",
    "ECOSTRESS",
    "ASTER_JPL",
    "EMIT_L2B",
    "KY_FIELD",
    "CUSTOM",
}

VALID_MEASUREMENT = {"LABORATORY", "FIELD", "AIRBORNE", "SPACEBORNE", "COMPUTED"}

CATALOG_COLUMNS = {
    "spectrum_id",
    "name",
    "material_category",
    "source_library",
    "quality",
    "material_name",
    "n_bands",
    "wavelength_min",
    "wavelength_max",
    "license",
    "citation",
    "instrument",
    "locality",
}

JSON_REQUIRED_FIELDS = {"spectrum_id", "name", "wavelengths", "reflectance", "metadata"}


def validate_hdf5(path: Path) -> list[str]:
    """Validate an HDF5 archive against the format spec.

    Checks dataset presence, array integrity, required attributes,
    and enum validity for every spectrum group in the archive.

    Args:
        path: Path to the HDF5 file.

    Returns:
        List of error strings. Empty list means fully conformant.
    """
    errors: list[str] = []

    with h5py.File(path, "r") as f:
        for cat_name in f:
            if cat_name == "metadata":
                continue
            if not isinstance(f[cat_name], h5py.Group):
                continue

            for spectrum_id in f[cat_name]:
                grp = f[cat_name][spectrum_id]
                prefix = f"/{cat_name}/{spectrum_id}"

                if "wavelengths" not in grp:
                    errors.append(f"{prefix}: missing required dataset 'wavelengths'")
                    continue
                if "reflectance" not in grp:
                    errors.append(f"{prefix}: missing required dataset 'reflectance'")
                    continue

                wl = np.array(grp["wavelengths"])
                refl = np.array(grp["reflectance"])

                if len(wl) != len(refl):
                    errors.append(
                        f"{prefix}: length mismatch — "
                        f"wavelengths={len(wl)}, reflectance={len(refl)}"
                    )

                if len(wl) > 1 and not np.all(np.diff(wl) >= 0):
                    errors.append(f"{prefix}: wavelengths not ascending")

                if "errors" in grp:
                    err_data = np.array(grp["errors"])
                    if len(err_data) != len(wl):
                        errors.append(
                            f"{prefix}: errors length mismatch — "
                            f"errors={len(err_data)}, wavelengths={len(wl)}"
                        )

                for attr in REQUIRED_ATTRS:
                    if attr not in grp.attrs:
                        errors.append(f"{prefix}: missing required attribute '{attr}'")

                quality = str(grp.attrs.get("quality", ""))
                if quality and quality not in VALID_QUALITY:
                    errors.append(f"{prefix}: invalid enum value quality='{quality}'")

                category = str(grp.attrs.get("material_category", ""))
                if category and category not in VALID_CATEGORY:
                    errors.append(f"{prefix}: invalid enum value material_category='{category}'")

                source = str(grp.attrs.get("source_library", ""))
                if source and source not in VALID_SOURCE:
                    errors.append(f"{prefix}: invalid enum value source_library='{source}'")

                mtype = str(grp.attrs.get("measurement_type", ""))
                if mtype and mtype not in VALID_MEASUREMENT:
                    errors.append(f"{prefix}: invalid enum value measurement_type='{mtype}'")

    return errors


def validate_parquet(path: Path) -> list[str]:
    """Validate Parquet query layer against the format spec.

    Checks that catalog.parquet contains all required columns and
    that per-spectrum Parquet files carry the minimum required fields.

    Args:
        path: Path to the Parquet directory (contains catalog.parquet
            and optionally a spectra/ subdirectory).

    Returns:
        List of error strings. Empty list means fully conformant.
    """
    errors: list[str] = []

    catalog_path = path / "catalog.parquet"
    if not catalog_path.exists():
        errors.append("catalog.parquet not found")
        return errors

    table = pq.read_table(catalog_path)
    actual_columns = set(table.column_names)

    for col in CATALOG_COLUMNS:
        if col not in actual_columns:
            errors.append(f"catalog.parquet: missing column '{col}'")

    spectra_dir = path / "spectra"
    if spectra_dir.exists():
        for pq_file in spectra_dir.glob("*.parquet"):
            t = pq.read_table(pq_file)
            cols = set(t.column_names)
            for required in ("spectrum_id", "name", "wavelengths", "reflectance"):
                if required not in cols:
                    errors.append(f"spectra/{pq_file.name}: missing column '{required}'")

    return errors


def validate_json(path: Path) -> list[str]:
    """Validate JSON catalog and spectrum files against the format spec.

    Checks that catalog.json is a JSON array and that individual
    spectrum JSON files carry all required top-level fields.

    Args:
        path: Path to the JSON directory (contains catalog.json and
            optionally a spectra/ subdirectory of individual files).

    Returns:
        List of error strings. Empty list means fully conformant.
    """
    errors: list[str] = []

    catalog_path = path / "catalog.json"
    if not catalog_path.exists():
        errors.append("catalog.json not found")
        return errors

    with catalog_path.open(encoding="utf-8") as f:
        catalog = json.load(f)

    if not isinstance(catalog, list):
        errors.append("catalog.json: expected JSON array, got " + type(catalog).__name__)
        return errors

    spectra_dir = path / "spectra"
    if spectra_dir.exists():
        for json_file in spectra_dir.glob("*.json"):
            with json_file.open(encoding="utf-8") as f:
                data = json.load(f)
            for field in JSON_REQUIRED_FIELDS:
                if field not in data:
                    errors.append(f"spectra/{json_file.name}: missing field '{field}'")

    return errors
