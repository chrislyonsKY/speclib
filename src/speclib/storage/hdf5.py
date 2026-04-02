"""HDF5 archival storage backend.

Source of truth for all spectral data. Organizes spectra
hierarchically by material category with per-spectrum attributes.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import h5py
import numpy as np

from speclib.core.metadata import SampleMetadata
from speclib.core.spectrum import MaterialCategory, QualityFlag, Spectrum

logger = logging.getLogger(__name__)


class HDF5Archive:
    """HDF5-based archival storage for the spectral library.

    Attributes:
        path: Path to the HDF5 archive file.
    """

    def __init__(self, path: Path) -> None:
        """Initialize HDF5 archive at the given path."""
        self.path = Path(path)

    def write(self, spectrum: Spectrum) -> None:
        """Write a single spectrum to the archive.

        Args:
            spectrum: Spectrum to store.
        """
        category = spectrum.metadata.material_category.value.lower()
        group_path = f"/{category}/{spectrum.spectrum_id}"

        with h5py.File(self.path, "a") as f:
            if group_path in f:
                del f[group_path]

            grp = f.create_group(group_path)
            grp.create_dataset(
                "wavelengths",
                data=spectrum.wavelengths,
                compression="gzip",
                compression_opts=4,
            )
            grp.create_dataset(
                "reflectance",
                data=spectrum.reflectance,
                compression="gzip",
                compression_opts=4,
            )
            if spectrum.errors is not None:
                grp.create_dataset(
                    "errors",
                    data=spectrum.errors,
                    compression="gzip",
                    compression_opts=4,
                )

            grp.attrs["name"] = spectrum.name
            grp.attrs["spectrum_id"] = spectrum.spectrum_id
            grp.attrs["quality"] = spectrum.quality.value

            meta_dict = spectrum.metadata.to_dict()
            for key, value in meta_dict.items():
                grp.attrs[key] = value

        logger.info("Wrote spectrum %s to %s", spectrum.spectrum_id, group_path)

    def read(self, spectrum_id: str) -> Spectrum:
        """Read a single spectrum from the archive.

        Args:
            spectrum_id: Unique spectrum identifier.

        Returns:
            Spectrum object with full data and metadata.

        Raises:
            KeyError: If spectrum_id is not found.
        """
        with h5py.File(self.path, "r") as f:
            grp = self._find_group(f, spectrum_id)
            if grp is None:
                msg = f"Spectrum {spectrum_id} not found in archive"
                raise KeyError(msg)

            wavelengths = np.array(grp["wavelengths"])
            reflectance = np.array(grp["reflectance"])
            errors = np.array(grp["errors"]) if "errors" in grp else None

            name = str(grp.attrs["name"])
            quality = QualityFlag(grp.attrs["quality"])

            skip_keys = {"name", "spectrum_id", "quality"}
            meta_dict = {k: grp.attrs[k] for k in grp.attrs if k not in skip_keys}
            metadata = SampleMetadata.from_dict(meta_dict)

            return Spectrum(
                name=name,
                wavelengths=wavelengths,
                reflectance=reflectance,
                metadata=metadata,
                quality=quality,
                errors=errors,
                spectrum_id=spectrum_id,
            )

    def list_ids(self, category: MaterialCategory | None = None) -> list[str]:
        """List all spectrum IDs, optionally filtered by category.

        Args:
            category: Optional material category filter.

        Returns:
            List of spectrum ID strings.
        """
        ids: list[str] = []
        if not self.path.exists():
            return ids

        with h5py.File(self.path, "r") as f:
            categories = [category.value.lower()] if category else list(f.keys())
            for cat_name in categories:
                if cat_name in f and isinstance(f[cat_name], h5py.Group):
                    for spectrum_id in f[cat_name]:
                        ids.append(spectrum_id)
        return ids

    def iterate(self) -> Iterator[Spectrum]:
        """Iterate over all spectra in the archive."""
        for sid in self.list_ids():
            yield self.read(sid)

    def _find_group(self, f: h5py.File, spectrum_id: str) -> h5py.Group | None:
        """Find a spectrum group by ID across all categories.

        Args:
            f: Open HDF5 file handle.
            spectrum_id: Spectrum ID to find.

        Returns:
            HDF5 group or None if not found.
        """
        for cat_name in f:
            if isinstance(f[cat_name], h5py.Group) and spectrum_id in f[cat_name]:
                return f[cat_name][spectrum_id]
        return None
