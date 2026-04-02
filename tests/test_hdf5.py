"""Tests for HDF5 archival storage backend."""

import tempfile
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
from speclib.storage.hdf5 import HDF5Archive


def _make_spectrum(name: str = "Test Quartz", category: str = "MINERAL") -> Spectrum:
    """Create a test spectrum."""
    return Spectrum(
        name=name,
        wavelengths=np.array([0.4, 0.5, 0.6, 0.7, 0.8]),
        reflectance=np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
        metadata=SampleMetadata(
            material_name="Quartz",
            material_category=MaterialCategory(category),
            source_library=SourceLibrary.USGS_SPLIB07,
            source_record_id="test_001",
            measurement_type=MeasurementType.LABORATORY,
            license="US Public Domain",
        ),
        quality=QualityFlag.GOOD,
    )


class TestHDF5Archive:
    """Tests for HDF5 write/read round-trip."""

    def test_write_and_read(self):
        """A spectrum can be written and read back identically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test.h5")
            spec = _make_spectrum()
            archive.write(spec)

            result = archive.read(spec.spectrum_id)
            assert result.name == spec.name
            assert result.spectrum_id == spec.spectrum_id
            np.testing.assert_array_almost_equal(result.wavelengths, spec.wavelengths)
            np.testing.assert_array_almost_equal(result.reflectance, spec.reflectance)
            assert result.quality == QualityFlag.GOOD

    def test_list_ids(self):
        """Written spectra appear in list_ids."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test.h5")
            spec = _make_spectrum()
            archive.write(spec)

            ids = archive.list_ids()
            assert spec.spectrum_id in ids

    def test_list_ids_empty(self):
        """Empty or nonexistent archive returns empty list."""
        archive = HDF5Archive(Path("nonexistent.h5"))
        assert archive.list_ids() == []

    def test_list_ids_by_category(self):
        """Filtering by category returns only matching spectra."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test.h5")
            archive.write(_make_spectrum("Quartz", "MINERAL"))
            archive.write(
                Spectrum(
                    name="Oak leaf",
                    wavelengths=np.array([0.4, 0.5, 0.6]),
                    reflectance=np.array([0.1, 0.3, 0.5]),
                    metadata=SampleMetadata(
                        material_name="Oak",
                        material_category=MaterialCategory.VEGETATION,
                        source_library=SourceLibrary.KY_FIELD,
                        source_record_id="oak_001",
                        measurement_type=MeasurementType.FIELD,
                        license="CC-BY-4.0",
                    ),
                )
            )

            mineral_ids = archive.list_ids(MaterialCategory.MINERAL)
            veg_ids = archive.list_ids(MaterialCategory.VEGETATION)
            assert len(mineral_ids) == 1
            assert len(veg_ids) == 1

    def test_read_nonexistent_raises(self):
        """Reading a nonexistent spectrum raises KeyError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test.h5")
            spec = _make_spectrum()
            archive.write(spec)
            import pytest

            with pytest.raises(KeyError):
                archive.read("does_not_exist")

    def test_metadata_round_trip(self):
        """Metadata survives write/read cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test.h5")
            spec = _make_spectrum()
            archive.write(spec)

            result = archive.read(spec.spectrum_id)
            assert result.metadata.material_name == "Quartz"
            assert result.metadata.source_library == SourceLibrary.USGS_SPLIB07
            assert result.metadata.license == "US Public Domain"
