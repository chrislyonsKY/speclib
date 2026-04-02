"""Parquet query layer -- derived from HDF5 archive.

Provides fast columnar search and filtering over the spectral catalog.
Regenerable from HDF5 via the build pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from speclib.storage.hdf5 import HDF5Archive

logger = logging.getLogger(__name__)


class ParquetStore:
    """Parquet-based query layer for the spectral library."""

    def __init__(self, path: Path) -> None:
        """Initialize Parquet store at the given directory path."""
        self.path = Path(path)

    def build_from_hdf5(self, archive: HDF5Archive) -> None:
        """Generate Parquet query files from HDF5 archive.

        Creates:
        - catalog.parquet: metadata-only searchable index
        - spectra/{category}.parquet: wavelength + reflectance as list columns

        Args:
            archive: Source HDF5 archive.
        """
        self.path.mkdir(parents=True, exist_ok=True)
        spectra_dir = self.path / "spectra"
        spectra_dir.mkdir(exist_ok=True)

        catalog_rows: list[dict[str, Any]] = []
        spectra_by_category: dict[str, list[dict[str, Any]]] = {}

        for spectrum in archive.iterate():
            catalog_rows.append(
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
                }
            )

            cat = spectrum.metadata.material_category.value.lower()
            if cat not in spectra_by_category:
                spectra_by_category[cat] = []
            spectra_by_category[cat].append(
                {
                    "spectrum_id": spectrum.spectrum_id,
                    "name": spectrum.name,
                    "wavelengths": spectrum.wavelengths.tolist(),
                    "reflectance": spectrum.reflectance.tolist(),
                }
            )

        # Write catalog
        if catalog_rows:
            catalog_table = pa.Table.from_pylist(catalog_rows)
            pq.write_table(
                catalog_table,
                self.path / "catalog.parquet",
                compression="snappy",
            )
            logger.info("Wrote catalog.parquet with %d entries", len(catalog_rows))

        # Write per-category spectra
        for cat, rows in spectra_by_category.items():
            table = pa.Table.from_pylist(rows)
            pq.write_table(
                table,
                spectra_dir / f"{cat}.parquet",
                compression="snappy",
            )
            logger.info("Wrote spectra/%s.parquet with %d spectra", cat, len(rows))

    def search(self, query: str, **filters: Any) -> list[dict[str, Any]]:
        """Search the Parquet catalog.

        Args:
            query: Text search string matched against name and material_name.
            **filters: Optional filters (category, source, quality, etc.).

        Returns:
            List of matching catalog entries as dicts.
        """
        catalog_path = self.path / "catalog.parquet"
        if not catalog_path.exists():
            return []

        table = pq.read_table(catalog_path)
        df_dict = table.to_pydict()
        n_rows = len(df_dict.get("spectrum_id", []))

        results: list[dict[str, Any]] = []
        query_lower = query.lower()

        for i in range(n_rows):
            row = {col: df_dict[col][i] for col in df_dict}

            # Text search on name and material_name
            name_match = query_lower in str(row.get("name", "")).lower()
            material_match = query_lower in str(row.get("material_name", "")).lower()
            if not (name_match or material_match):
                continue

            # Apply filters
            skip = False
            for key, value in filters.items():
                if key in row and row[key] != value:
                    skip = True
                    break
            if skip:
                continue

            results.append(row)

        return results
