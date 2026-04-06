"""Tests for JSON export format."""

import json
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
from speclib.export.json_export import batch_write, write


def _make_spectrum(name: str = "Quartz SiO2", category: str = "MINERAL") -> Spectrum:
    """Create a test spectrum."""
    return Spectrum(
        name=name,
        wavelengths=np.array([0.4, 0.5, 0.6, 0.7, 0.8]),
        reflectance=np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
        metadata=SampleMetadata(
            material_name=name,
            material_category=MaterialCategory(category),
            source_library=SourceLibrary.ECOSTRESS,
            source_record_id="test_001",
            measurement_type=MeasurementType.LABORATORY,
            license="CC0 / Public Domain",
            description="Test spectrum",
            locality="Test location",
            citation="Test citation",
        ),
        quality=QualityFlag.GOOD,
    )


class TestJsonWrite:
    """Tests for single spectrum JSON export."""

    def test_write_creates_file(self):
        """write() creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            write(_make_spectrum(), path)
            assert path.exists()

    def test_write_valid_json(self):
        """Output is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            write(_make_spectrum(), path)
            data = json.loads(path.read_text())
            assert isinstance(data, dict)

    def test_write_has_required_fields(self):
        """JSON contains spectrum_id, name, wavelengths, reflectance, metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            write(_make_spectrum(), path)
            data = json.loads(path.read_text())
            assert "spectrum_id" in data
            assert "name" in data
            assert "wavelengths" in data
            assert "reflectance" in data
            assert "metadata" in data

    def test_write_wavelengths_are_list(self):
        """Wavelengths are serialized as a JSON array of floats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            spec = _make_spectrum()
            write(spec, path)
            data = json.loads(path.read_text())
            assert data["wavelengths"] == [0.4, 0.5, 0.6, 0.7, 0.8]
            assert data["reflectance"] == [0.1, 0.2, 0.3, 0.4, 0.5]

    def test_write_metadata_fields(self):
        """Metadata block contains expected fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            write(_make_spectrum(), path)
            data = json.loads(path.read_text())
            meta = data["metadata"]
            assert meta["material_category"] == "MINERAL"
            assert meta["source_library"] == "ECOSTRESS"
            assert meta["quality"] == "GOOD"
            assert meta["measurement_type"] == "LABORATORY"


class TestJsonBatchWrite:
    """Tests for batch JSON export (catalog + individual files)."""

    def test_batch_creates_catalog(self):
        """batch_write() creates catalog.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            batch_write([_make_spectrum()], out)
            assert (out / "catalog.json").exists()

    def test_batch_creates_spectrum_files(self):
        """batch_write() creates spectra/{id}.json for each spectrum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            spec = _make_spectrum()
            batch_write([spec], out)
            assert (out / "spectra" / f"{spec.spectrum_id}.json").exists()

    def test_batch_catalog_is_array(self):
        """catalog.json is a JSON array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            batch_write([_make_spectrum(), _make_spectrum("Oak Leaf", "VEGETATION")], out)
            data = json.loads((out / "catalog.json").read_text())
            assert isinstance(data, list)
            assert len(data) == 2

    def test_batch_catalog_has_metadata_fields(self):
        """Each catalog entry has the expected metadata fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            batch_write([_make_spectrum()], out)
            data = json.loads((out / "catalog.json").read_text())
            entry = data[0]
            assert "spectrum_id" in entry
            assert "name" in entry
            assert "material_category" in entry
            assert "wavelength_min" in entry
            assert "wavelength_max" in entry
            assert "n_bands" in entry
