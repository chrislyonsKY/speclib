"""Export adapter: ascii format.

TODO: Implement write/batch_write for ascii format.
"""

from __future__ import annotations

from pathlib import Path

from speclib.core.spectrum import Spectrum


def write(spectrum: Spectrum, path: Path) -> None:
    """Write a single spectrum to ascii format.

    Args:
        spectrum: Spectrum to export.
        path: Output file path.
    """
    # TODO: Implement
    raise NotImplementedError


def batch_write(spectra: list[Spectrum], path: Path) -> None:
    """Write multiple spectra to ascii format.

    Args:
        spectra: List of spectra to export.
        path: Output file or directory path.
    """
    # TODO: Implement
    raise NotImplementedError
