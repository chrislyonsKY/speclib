"""Spectral convolution and resampling engine.

Implements the USGS splib07b methodology: cubic-spline oversampling
followed by Gaussian convolution with sensor response functions.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from speclib.core.spectrum import Spectrum


def load_sensor_response(sensor: str | Path) -> dict:
    """Load a sensor spectral response function.

    Args:
        sensor: Sensor name (e.g., 'L8_OLI') or path to custom RSR YAML.

    Returns:
        Dictionary with 'channels' list of {center_wavelength, fwhm, name}.
    """
    # TODO: Load from data/sensors/ YAML files
    # TODO: Support custom YAML paths
    raise NotImplementedError


def oversample(wavelengths: np.ndarray, reflectance: np.ndarray,
               target_spacing: float = 0.0001) -> tuple[np.ndarray, np.ndarray]:
    """Oversample spectrum via cubic-spline interpolation (splib07b method).

    Args:
        wavelengths: Original wavelength array (µm).
        reflectance: Original reflectance array.
        target_spacing: Target wavelength spacing in µm.

    Returns:
        Tuple of (oversampled_wavelengths, oversampled_reflectance).
    """
    # TODO: Cubic spline interpolation
    # TODO: Handle NaN gaps (don't interpolate across them)
    raise NotImplementedError


def convolve_gaussian(wavelengths: np.ndarray, reflectance: np.ndarray,
                      center: float, fwhm: float) -> float:
    """Convolve spectrum with a Gaussian response function for one band.

    Args:
        wavelengths: Oversampled wavelength array.
        reflectance: Oversampled reflectance array.
        center: Center wavelength of the band (µm).
        fwhm: Full width at half maximum of the Gaussian (µm).

    Returns:
        Convolved reflectance value for this band.
    """
    # TODO: Gaussian convolution
    raise NotImplementedError


def resample_spectrum(spectrum: Spectrum, sensor: str | Path) -> Spectrum:
    """Resample a spectrum to a target sensor's spectral characteristics.

    Args:
        spectrum: Input spectrum (native resolution).
        sensor: Sensor name or path to custom RSR YAML.

    Returns:
        New Spectrum resampled to target sensor bands.
    """
    # TODO: Load sensor response
    # TODO: Oversample input spectrum
    # TODO: Convolve each band
    # TODO: Return new Spectrum with effective wavelengths
    raise NotImplementedError
