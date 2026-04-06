"""Export adapter: JSON format for static web viewer.

Produces individual spectrum JSON files and a catalog index
following the speclib format specification section 3.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from speclib.core.spectrum import Spectrum

logger = logging.getLogger(__name__)


def write(spectrum: Spectrum, path: Path) -> None:
    """Write a single spectrum to JSON format.

    Args:
        spectrum: Spectrum to export.
        path: Output file path.
    """
    data = _spectrum_to_dict(spectrum)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def batch_write(spectra: list[Spectrum], path: Path) -> None:
    """Write catalog.json and individual spectrum files.

    Args:
        spectra: List of spectra to export.
        path: Output directory path.
    """
    path.mkdir(parents=True, exist_ok=True)
    spectra_dir = path / "spectra"
    spectra_dir.mkdir(exist_ok=True)

    catalog: list[dict] = []
    for spectrum in spectra:
        write(spectrum, spectra_dir / f"{spectrum.spectrum_id}.json")

        catalog.append(
            {
                "spectrum_id": spectrum.spectrum_id,
                "name": spectrum.name,
                "material_category": spectrum.metadata.material_category.value,
                "source_library": spectrum.metadata.source_library.value,
                "quality": spectrum.quality.value,
                "material_name": spectrum.metadata.material_name,
                "n_bands": spectrum.n_bands,
                "wavelength_min": float(spectrum.wavelength_range[0]),
                "wavelength_max": float(spectrum.wavelength_range[1]),
                "license": spectrum.metadata.license,
                "citation": spectrum.metadata.citation,
                "instrument": spectrum.metadata.instrument,
                "locality": spectrum.metadata.locality,
                "measurement_type": spectrum.metadata.measurement_type.value,
            }
        )

    with (path / "catalog.json").open("w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    logger.info(
        "Wrote catalog.json with %d entries and %d spectrum files",
        len(catalog),
        len(spectra),
    )


def _spectrum_to_dict(spectrum: Spectrum) -> dict:
    """Convert a Spectrum to the JSON format defined in format-spec section 3.2.

    Args:
        spectrum: Spectrum to serialize.

    Returns:
        Dictionary matching the JSON schema.
    """
    return {
        "spectrum_id": spectrum.spectrum_id,
        "name": spectrum.name,
        "wavelengths": spectrum.wavelengths.tolist(),
        "reflectance": spectrum.reflectance.tolist(),
        "metadata": {
            "material_category": spectrum.metadata.material_category.value,
            "source_library": spectrum.metadata.source_library.value,
            "quality": spectrum.quality.value,
            "material_name": spectrum.metadata.material_name,
            "source_record_id": spectrum.metadata.source_record_id,
            "measurement_type": spectrum.metadata.measurement_type.value,
            "license": spectrum.metadata.license,
            "description": spectrum.metadata.description,
            "locality": spectrum.metadata.locality,
            "citation": spectrum.metadata.citation,
        },
    }
