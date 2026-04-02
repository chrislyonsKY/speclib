"""Tests for core Spectrum data model."""

import numpy as np
import pytest

from speclib.core.spectrum import MaterialCategory, QualityFlag, SourceLibrary, Spectrum


class TestSpectrum:
    """Tests for Spectrum construction and validation."""

    # TODO: Test valid spectrum creation
    # TODO: Test wavelengths must be sorted ascending
    # TODO: Test wavelengths and reflectance must be same length
    # TODO: Test reflectance out-of-range flagging
    # TODO: Test spectrum_id auto-generation
    # TODO: Test n_bands property
    # TODO: Test wavelength_range property
    pass


class TestQualityFlag:
    """Tests for QualityFlag enum."""

    # TODO: Test all enum values exist
    # TODO: Test string conversion
    pass


class TestMaterialCategory:
    """Tests for MaterialCategory enum including KY categories."""

    # TODO: Test all categories including KY_INVASIVE, KY_MINERAL, KY_RECLAMATION
    pass
