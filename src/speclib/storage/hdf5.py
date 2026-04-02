"""HDF5 archival storage backend.

Source of truth for all spectral data. Organizes spectra
hierarchically by material category with per-spectrum attributes.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from speclib.core.spectrum import MaterialCategory, Spectrum

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
        # TODO: Open HDF5, create group path, write arrays + attrs
        # TODO: gzip compression level 4
        raise NotImplementedError

    def read(self, spectrum_id: str) -> Spectrum:
        """Read a single spectrum from the archive.

        Args:
            spectrum_id: Unique spectrum identifier.

        Returns:
            Spectrum object with full data and metadata.
        """
        # TODO: Locate dataset by ID, read arrays + attrs, construct Spectrum
        raise NotImplementedError

    def list_ids(self, category: MaterialCategory | None = None) -> list[str]:
        """List all spectrum IDs, optionally filtered by category.

        Args:
            category: Optional material category filter.

        Returns:
            List of spectrum ID strings.
        """
        # TODO: Walk HDF5 groups, collect IDs
        raise NotImplementedError

    def iterate(self) -> Iterator[Spectrum]:
        """Iterate over all spectra in the archive."""
        for sid in self.list_ids():
            yield self.read(sid)
