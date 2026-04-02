"""Matplotlib spectral plotting utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speclib.core.spectrum import Spectrum


def plot_spectrum(spectrum: Spectrum, ax=None, show_errors: bool = False, **kwargs):
    """Plot a single spectrum.

    Args:
        spectrum: Spectrum to plot.
        ax: Optional matplotlib Axes.
        show_errors: Whether to show error bars.
        **kwargs: Passed to ax.plot().
    """
    # TODO: Implement
    raise NotImplementedError


def plot_comparison(spectra: list[Spectrum], ax=None, **kwargs):
    """Overlay multiple spectra for comparison.

    Args:
        spectra: List of spectra to overlay (max 6 recommended).
        ax: Optional matplotlib Axes.
        **kwargs: Passed to ax.plot().
    """
    # TODO: Implement with distinct line styles + colors
    # TODO: Use line styles (not just color) per WCAG compliance
    raise NotImplementedError
