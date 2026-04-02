"""SpectralLibrary collection — search, filter, iterate over spectra.

Provides the main entry point for working with a spectral library
as a collection of Spectrum objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from speclib.core.spectrum import MaterialCategory, QualityFlag, SourceLibrary, Spectrum


class SpectralLibrary:
    """A searchable collection of Spectrum objects.

    Supports loading from HDF5 archives and Parquet query layers,
    with search, filter, and iteration capabilities.
    """

    def __init__(self) -> None:
        """Initialize an empty spectral library."""
        # TODO: Internal storage (list or dict keyed by spectrum_id)
        self._spectra: dict[str, Spectrum] = {}

    @classmethod
    def from_hdf5(cls, path: str | Path) -> SpectralLibrary:
        """Load a spectral library from an HDF5 archive.

        Args:
            path: Path to the HDF5 archive file.

        Returns:
            Populated SpectralLibrary instance.
        """
        # TODO: Open HDF5 file, iterate groups, construct Spectrum objects
        raise NotImplementedError

    @classmethod
    def from_parquet(cls, path: str | Path) -> SpectralLibrary:
        """Load a spectral library from Parquet query layer.

        Args:
            path: Path to the Parquet directory or catalog file.

        Returns:
            Populated SpectralLibrary instance.
        """
        # TODO: Read Parquet catalog + spectra files via pyarrow
        raise NotImplementedError

    def search(
        self,
        query: str,
        category: str | MaterialCategory | None = None,
        source: str | SourceLibrary | None = None,
        quality: str | QualityFlag | None = None,
        wavelength_range: tuple[float, float] | None = None,
    ) -> list[Spectrum]:
        """Search the library by name and optional filters.

        Args:
            query: Text search against spectrum names and material names.
            category: Filter by material category.
            source: Filter by source library.
            quality: Minimum quality flag.
            wavelength_range: Filter by wavelength coverage (min, max) in µm.

        Returns:
            List of matching Spectrum objects.
        """
        # TODO: Implement search with filters
        raise NotImplementedError

    def __len__(self) -> int:
        """Number of spectra in the library."""
        return len(self._spectra)

    def __iter__(self) -> Iterator[Spectrum]:
        """Iterate over all spectra."""
        return iter(self._spectra.values())

    def __getitem__(self, spectrum_id: str) -> Spectrum:
        """Get a spectrum by ID."""
        return self._spectra[spectrum_id]
