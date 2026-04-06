"""Conformance tests: validate reference archive against format spec.

These tests require the reference fixtures to be pre-built by running:

    python tests/conformance/build_reference.py

If the reference archive does not exist (e.g. in a fresh clone before
running the build script), every test in this module is automatically
skipped rather than failing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conformance.validate import validate_hdf5, validate_json, validate_parquet

CONFORMANCE_DIR = Path(__file__).parent / "conformance"
REFERENCE_HDF5 = CONFORMANCE_DIR / "reference.h5"
REFERENCE_PARQUET = CONFORMANCE_DIR / "reference" / "parquet"
REFERENCE_JSON = CONFORMANCE_DIR / "reference" / "json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def reference_archive() -> Path:
    """Path to the reference HDF5 archive.

    Returns:
        Path to the pre-built reference.h5 file.
    """
    if not REFERENCE_HDF5.exists():
        pytest.skip(
            "Reference archive not built — run: python tests/conformance/build_reference.py"
        )
    return REFERENCE_HDF5


@pytest.fixture()
def reference_parquet() -> Path:
    """Path to the reference Parquet directory.

    Returns:
        Path to the pre-built parquet/ directory.
    """
    if not REFERENCE_PARQUET.exists():
        pytest.skip(
            "Reference Parquet not built — run: python tests/conformance/build_reference.py"
        )
    return REFERENCE_PARQUET


@pytest.fixture()
def reference_json() -> Path:
    """Path to the reference JSON directory.

    Returns:
        Path to the pre-built json/ directory.
    """
    if not REFERENCE_JSON.exists():
        pytest.skip("Reference JSON not built — run: python tests/conformance/build_reference.py")
    return REFERENCE_JSON


# ---------------------------------------------------------------------------
# HDF5 conformance
# ---------------------------------------------------------------------------


class TestHDF5Conformance:
    """Validate HDF5 archive structure and content against the format spec."""

    def test_all_spectra_have_required_attributes(self, reference_archive: Path) -> None:
        """Every spectrum group carries all required attributes."""
        errors = validate_hdf5(reference_archive)
        attr_errors = [e for e in errors if "missing required attribute" in e]
        assert attr_errors == [], "Missing attributes:\n" + "\n".join(attr_errors)

    def test_wavelengths_ascending(self, reference_archive: Path) -> None:
        """All wavelength datasets are sorted strictly ascending."""
        errors = validate_hdf5(reference_archive)
        wl_errors = [e for e in errors if "wavelengths not ascending" in e]
        assert wl_errors == [], "Wavelength ordering errors:\n" + "\n".join(wl_errors)

    def test_datasets_same_length(self, reference_archive: Path) -> None:
        """Wavelengths and reflectance arrays have matching lengths."""
        errors = validate_hdf5(reference_archive)
        len_errors = [e for e in errors if "length mismatch" in e]
        assert len_errors == [], "Array length errors:\n" + "\n".join(len_errors)

    def test_enum_values_valid(self, reference_archive: Path) -> None:
        """All enum attributes contain recognised values."""
        errors = validate_hdf5(reference_archive)
        enum_errors = [e for e in errors if "invalid enum value" in e]
        assert enum_errors == [], "Enum validation errors:\n" + "\n".join(enum_errors)

    def test_no_errors(self, reference_archive: Path) -> None:
        """Full HDF5 validation reports zero errors."""
        errors = validate_hdf5(reference_archive)
        assert errors == [], "Validation errors:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Parquet conformance
# ---------------------------------------------------------------------------


class TestParquetConformance:
    """Validate Parquet query-layer files against the format spec."""

    def test_catalog_has_required_columns(self, reference_parquet: Path) -> None:
        """catalog.parquet contains every required metadata column."""
        errors = validate_parquet(reference_parquet)
        col_errors = [e for e in errors if "missing column" in e]
        assert col_errors == [], "Missing columns:\n" + "\n".join(col_errors)

    def test_no_errors(self, reference_parquet: Path) -> None:
        """Full Parquet validation reports zero errors."""
        errors = validate_parquet(reference_parquet)
        assert errors == [], "Validation errors:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# JSON conformance
# ---------------------------------------------------------------------------


class TestJsonConformance:
    """Validate JSON catalog and spectrum files against the format spec."""

    def test_catalog_is_array(self, reference_json: Path) -> None:
        """catalog.json is a top-level JSON array."""
        errors = validate_json(reference_json)
        array_errors = [e for e in errors if "catalog.json" in e and "array" in e]
        assert array_errors == [], "Catalog structure errors:\n" + "\n".join(array_errors)

    def test_spectrum_files_have_required_fields(self, reference_json: Path) -> None:
        """Individual spectrum JSON files carry all required top-level fields."""
        errors = validate_json(reference_json)
        field_errors = [e for e in errors if "missing field" in e]
        assert field_errors == [], "Missing fields:\n" + "\n".join(field_errors)

    def test_no_errors(self, reference_json: Path) -> None:
        """Full JSON validation reports zero errors."""
        errors = validate_json(reference_json)
        assert errors == [], "Validation errors:\n" + "\n".join(errors)
