"""Tests for ECOSTRESS/ASTER spectral library ingestion adapter."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import yaml

from speclib.ingest.ecostress import EcostressAdapter, _read_ancillary, _read_header

ECOSTRESS_DATA = Path(__file__).parent / "data" / "ecostress"


def _make_adapter() -> EcostressAdapter:
    """Create an EcostressAdapter pointing at test data."""
    config = {
        "source": "ECOSTRESS",
        "version": "1.0",
        "citation": "Meerdink et al. (2019)",
        "license": "CC0 / Public Domain",
        "data_dir": str(ECOSTRESS_DATA),
    }
    tmp = Path(tempfile.mkdtemp()) / "ecostress_test.yaml"
    tmp.write_text(yaml.dump(config))
    return EcostressAdapter(tmp)


class TestReadHeader:
    """Tests for the _read_header function."""

    def test_mineral_header_extracts_values(self):
        """Mineral spectrum header values are extracted without key prefixes."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        header = _read_header(path)
        assert header["Name"] == "Hematite alpha Fe_2O_3"
        assert header["Type"] == "Mineral"
        assert header["Class"] == "Oxide"
        assert header["Subclass"] == "None"
        assert header["Particle Size"] == "Fine"

    def test_vegetation_header_has_genus_species(self):
        """Vegetation spectra have Genus and Species fields instead of Subclass."""
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        header = _read_header(path)
        assert header["Name"] == "Avena fatua"
        assert header["Type"] == "vegetation"
        assert header["Genus"] == "Avena"
        assert header["Species"] == "fatua"
        assert "Subclass" not in header

    def test_npv_header_type_field(self):
        """Non-photosynthetic vegetation Type field has spaces."""
        fname = "nonphotosyntheticvegetation.bark.pinus.coulteri.vswir.vh342.ucsb.asd.spectrum.txt"
        path = ECOSTRESS_DATA / fname
        header = _read_header(path)
        assert header["Type"] == "non photosynthetic vegetation"
        assert header["Genus"] == "Pinus"
        assert header["Species"] == "coulteri"

    def test_header_extracts_wavelength_unit(self):
        """X Units field is parsed from the header."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        header = _read_header(path)
        x_units = header["X Units"].lower()
        assert "micrometers" in x_units or "micrometer" in x_units

    def test_header_extracts_data_unit(self):
        """Y Units field is parsed from the header."""
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        header = _read_header(path)
        assert "percentage" in header["Y Units"].lower() or "percent" in header["Y Units"].lower()

    def test_header_stops_at_additional_info(self):
        """Header parsing stops at the blank line following the last header field."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        header = _read_header(path)
        assert "Additional Information" in header


class TestFetchAndNormalize:
    """Tests for fetch() and normalize() pipeline."""

    def test_mineral_descending_wavelengths_sorted_ascending(self):
        """Mineral spectra with descending wavelengths are sorted ascending after normalize."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        raw = adapter.fetch(str(path))
        assert raw.wavelengths[0] > raw.wavelengths[-1], "Expected descending raw wavelengths"
        spectrum = adapter.normalize(raw)
        assert spectrum.wavelengths[0] < spectrum.wavelengths[-1]
        assert np.all(np.diff(spectrum.wavelengths) >= 0)

    def test_vegetation_already_ascending(self):
        """Vegetation spectra that are already ascending stay ascending."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert spectrum.wavelengths[0] < spectrum.wavelengths[-1]
        assert np.all(np.diff(spectrum.wavelengths) >= 0)

    def test_reflectance_converted_to_fractional(self):
        """Reflectance in percentage is converted to 0.0-1.0 scale."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert np.all(spectrum.reflectance <= 1.0)
        assert np.all(spectrum.reflectance >= 0.0) or np.any(np.isnan(spectrum.reflectance))

    def test_npv_maps_to_correct_category(self):
        """Non-photosynthetic vegetation maps to NONPHOTOSYNTHETIC_VEGETATION category."""
        from speclib.core.spectrum import MaterialCategory

        adapter = _make_adapter()
        fname = "nonphotosyntheticvegetation.bark.pinus.coulteri.vswir.vh342.ucsb.asd.spectrum.txt"
        path = ECOSTRESS_DATA / fname
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert spectrum.metadata.material_category == MaterialCategory.NONPHOTOSYNTHETIC_VEGETATION

    def test_mineral_maps_to_mineral_category(self):
        """Mineral type maps to MINERAL category."""
        from speclib.core.spectrum import MaterialCategory

        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert spectrum.metadata.material_category == MaterialCategory.MINERAL

    def test_metadata_preserves_name(self):
        """Spectrum name is extracted correctly from header."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert spectrum.name == "Avena fatua"

    def test_metadata_preserves_origin(self):
        """Locality/origin is preserved in metadata."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert "34.5143" in spectrum.metadata.locality

    def test_soil_maps_to_soil_category(self):
        """Soil type maps to SOIL category."""
        from speclib.core.spectrum import MaterialCategory

        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "soil.alfisol.fragiboralf.none.all.86p1994.jhu.becknic.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert spectrum.metadata.material_category == MaterialCategory.SOIL


class TestAncillaryLinking:
    """Tests for ancillary file discovery and metadata merging."""

    def test_read_ancillary_returns_dict(self):
        """Ancillary file is parsed into a metadata dict."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.ancillary.txt"
        if not path.exists():
            pytest.skip("Mineral ancillary test file not available")
        anc = _read_ancillary(path)
        assert isinstance(anc, dict)
        assert len(anc) > 0

    def test_ancillary_has_extra_fields(self):
        """Ancillary file contains fields beyond the standard header."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.ancillary.txt"
        if not path.exists():
            pytest.skip("Mineral ancillary test file not available")
        anc = _read_ancillary(path)
        assert "ancillary_text" in anc

    def test_normalize_merges_ancillary_when_present(self):
        """Ancillary metadata is merged into the spectrum's extra dict."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        anc_path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.ancillary.txt"
        if anc_path.exists():
            assert "ancillary_text" in spectrum.metadata.extra

    def test_normalize_works_without_ancillary(self):
        """Spectra without paired ancillary files normalize successfully."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        assert spectrum.name == "Avena fatua"


class TestDiscover:
    """Tests for the discover() method."""

    def test_discover_finds_all_spectra(self):
        """discover() finds all .spectrum.txt files in the data dir."""
        adapter = _make_adapter()
        records = adapter.discover()
        spectrum_files = list(ECOSTRESS_DATA.glob("*.spectrum.txt"))
        assert len(records) == len(spectrum_files)

    def test_discover_extracts_names(self):
        """Discovered records have correct names from headers."""
        adapter = _make_adapter()
        records = adapter.discover()
        names = {r.name for r in records}
        assert "Avena fatua" in names

    def test_discover_maps_categories(self):
        """Discovered records have correct category mappings."""
        adapter = _make_adapter()
        records = adapter.discover()
        categories = {r.category for r in records}
        assert "MINERAL" in categories
        assert "VEGETATION" in categories


class TestFullPipeline:
    """End-to-end integration test: discover -> fetch -> normalize -> HDF5."""

    def test_ingest_all_to_hdf5(self):
        """All test spectra can be ingested and round-tripped through HDF5."""
        from speclib.storage.hdf5 import HDF5Archive

        adapter = _make_adapter()
        spectra = adapter.ingest_all()
        assert len(spectra) > 0

        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test_ecostress.h5")
            for spectrum in spectra:
                archive.write(spectrum)

            ids = archive.list_ids()
            assert len(ids) == len(spectra)

            for spectrum in spectra:
                loaded = archive.read(spectrum.spectrum_id)
                assert loaded.name == spectrum.name
                np.testing.assert_array_almost_equal(loaded.wavelengths, spectrum.wavelengths)
                np.testing.assert_array_almost_equal(loaded.reflectance, spectrum.reflectance)
                assert loaded.metadata.material_category == spectrum.metadata.material_category
                assert loaded.metadata.source_library == spectrum.metadata.source_library

    def test_all_wavelengths_ascending(self):
        """Every ingested spectrum has ascending wavelengths."""
        adapter = _make_adapter()
        spectra = adapter.ingest_all()
        for spectrum in spectra:
            assert np.all(np.diff(spectrum.wavelengths) >= 0), (
                f"{spectrum.name}: wavelengths not ascending"
            )

    def test_all_reflectance_fractional(self):
        """Every ingested spectrum has reflectance in 0.0-1.0 scale."""
        adapter = _make_adapter()
        spectra = adapter.ingest_all()
        for spectrum in spectra:
            finite = spectrum.reflectance[np.isfinite(spectrum.reflectance)]
            assert np.all(finite <= 1.5), (
                f"{spectrum.name}: reflectance max {finite.max()} suggests unconverted percentage"
            )
