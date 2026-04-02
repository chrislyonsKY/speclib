"""speclib — Federated spectral signature library.

A platform for aggregating, searching, and distributing reflectance
spectra from major public repositories with Kentucky-focused collections.
"""

__version__ = "1.0.0"

from speclib.core.spectrum import (
    MaterialCategory,
    MeasurementType,
    QualityFlag,
    SourceLibrary,
    Spectrum,
)

# TODO: Import SpectralLibrary once implemented
# from speclib.core.library import SpectralLibrary

__all__ = [
    "MaterialCategory",
    "MeasurementType",
    "QualityFlag",
    "SourceLibrary",
    "Spectrum",
    "__version__",
]
