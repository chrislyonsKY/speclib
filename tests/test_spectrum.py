"""Tests for core Spectrum data model."""

import numpy as np

from speclib.core.spectrum import (
    MaterialCategory,
    MeasurementType,
    QualityFlag,
    SourceLibrary,
    Spectrum,
)


def _make_metadata():
    """Create a minimal SampleMetadata for testing."""
    from speclib.core.metadata import SampleMetadata

    return SampleMetadata(
        material_name="Quartz",
        material_category=MaterialCategory.MINERAL,
        source_library=SourceLibrary.USGS_SPLIB07,
        source_record_id="test_001",
        measurement_type=MeasurementType.LABORATORY,
        license="US Public Domain",
    )


class TestQualityFlag:
    """Tests for QualityFlag enum."""

    def test_all_values_exist(self):
        """All expected quality flag values are defined."""
        expected = {"VERIFIED", "GOOD", "FAIR", "POOR", "SUSPECT", "DERIVED"}
        actual = {f.value for f in QualityFlag}
        assert actual == expected

    def test_string_value(self):
        """Quality flags use their name as value."""
        assert QualityFlag.GOOD.value == "GOOD"


class TestMaterialCategory:
    """Tests for MaterialCategory enum including KY categories."""

    def test_ky_categories_exist(self):
        """Kentucky-specific categories are defined."""
        assert MaterialCategory.KY_INVASIVE.value == "KY_INVASIVE"
        assert MaterialCategory.KY_MINERAL.value == "KY_MINERAL"
        assert MaterialCategory.KY_RECLAMATION.value == "KY_RECLAMATION"

    def test_standard_categories(self):
        """Standard USGS categories are defined."""
        assert MaterialCategory.MINERAL.value == "MINERAL"
        assert MaterialCategory.VEGETATION.value == "VEGETATION"
        assert MaterialCategory.SOIL.value == "SOIL"

    def test_nonphotosynthetic_vegetation_category(self):
        """Non-photosynthetic vegetation category is defined."""
        assert MaterialCategory.NONPHOTOSYNTHETIC_VEGETATION.value == "NONPHOTOSYNTHETIC_VEGETATION"


class TestSourceLibrary:
    """Tests for SourceLibrary enum."""

    def test_all_sources(self):
        """All upstream sources are defined."""
        expected = {"USGS_SPLIB07", "ECOSTRESS", "ASTER_JPL", "EMIT_L2B", "KY_FIELD", "CUSTOM"}
        actual = {s.value for s in SourceLibrary}
        assert actual == expected


class TestSpectrum:
    """Tests for Spectrum construction and basic properties."""

    def test_create_valid_spectrum(self):
        """A valid spectrum can be constructed."""
        spec = Spectrum(
            name="Quartz GDS74",
            wavelengths=np.array([0.4, 0.5, 0.6, 0.7]),
            reflectance=np.array([0.1, 0.2, 0.3, 0.4]),
            metadata=_make_metadata(),
        )
        assert spec.name == "Quartz GDS74"
        assert spec.quality == QualityFlag.GOOD

    def test_n_bands(self):
        """The n_bands property returns wavelength count."""
        spec = Spectrum(
            name="Test",
            wavelengths=np.array([0.4, 0.5, 0.6]),
            reflectance=np.array([0.1, 0.2, 0.3]),
            metadata=_make_metadata(),
        )
        assert spec.n_bands == 3

    def test_wavelength_range(self):
        """The wavelength_range property returns min/max tuple."""
        spec = Spectrum(
            name="Test",
            wavelengths=np.array([0.35, 0.5, 2.5]),
            reflectance=np.array([0.1, 0.2, 0.3]),
            metadata=_make_metadata(),
        )
        assert spec.wavelength_range == (0.35, 2.5)

    def test_generate_id_deterministic(self):
        """The same inputs always produce the same spectrum ID."""
        id1 = Spectrum._generate_id("USGS_SPLIB07", "MINERAL", "Quartz GDS74")
        id2 = Spectrum._generate_id("USGS_SPLIB07", "MINERAL", "Quartz GDS74")
        assert id1 == id2
        assert "usgs_splib07_mineral_" in id1
