"""Build the conformance reference archive from the live speclib archive.

Extracts one representative spectrum per populated category from the live
archive, writes a small reference HDF5, then generates expected Parquet
and JSON outputs alongside it.

The reference fixtures live in tests/conformance/reference/ and are used
by the conformance test suite.  They are NOT committed to git (HDF5 and
Parquet files are in .gitignore); run this script once after cloning or
after the live archive changes.

Usage:
    python tests/conformance/build_reference.py

    Or from the project root:
    python -m tests.conformance.build_reference
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Allow running from the project root without installing the package
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from speclib.core.spectrum import MaterialCategory  # noqa: E402
from speclib.export.json_export import batch_write  # noqa: E402
from speclib.storage.hdf5 import HDF5Archive  # noqa: E402
from speclib.storage.parquet import ParquetStore  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

LIVE_ARCHIVE = project_root / "data" / "speclib_archive.h5"
CONFORMANCE_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = CONFORMANCE_DIR / "reference"
REFERENCE_HDF5 = CONFORMANCE_DIR / "reference.h5"
REFERENCE_PARQUET = REFERENCE_DIR / "parquet"
REFERENCE_JSON = REFERENCE_DIR / "json"


def main() -> None:
    """Build reference conformance fixtures from the live archive.

    Raises:
        SystemExit: If the live archive does not exist.
    """
    if not LIVE_ARCHIVE.exists():
        logger.error("Live archive not found: %s", LIVE_ARCHIVE)
        logger.error("Run the ingestion pipeline first to populate the archive.")
        sys.exit(1)

    logger.info("Reading live archive: %s", LIVE_ARCHIVE)
    live = HDF5Archive(LIVE_ARCHIVE)

    # Remove stale reference archive before rebuilding
    if REFERENCE_HDF5.exists():
        REFERENCE_HDF5.unlink()
        logger.info("Removed stale reference archive")

    ref = HDF5Archive(REFERENCE_HDF5)

    spectra = []
    skipped = []
    for cat in MaterialCategory:
        ids = live.list_ids(cat)
        if not ids:
            skipped.append(cat.value)
            continue
        spectrum = live.read(ids[0])
        ref.write(spectrum)
        spectra.append(spectrum)
        logger.info("  [%s] %s (%d bands)", cat.value, spectrum.name, spectrum.n_bands)

    logger.info(
        "Reference archive: %d spectra from %d populated categories",
        len(spectra),
        len(spectra),
    )
    if skipped:
        logger.info("Skipped empty categories: %s", ", ".join(skipped))

    # Build Parquet query layer from the reference archive
    logger.info("Building Parquet query layer: %s", REFERENCE_PARQUET)
    parquet = ParquetStore(REFERENCE_PARQUET)
    parquet.build_from_hdf5(ref)

    # Build JSON export
    logger.info("Building JSON export: %s", REFERENCE_JSON)
    batch_write(spectra, REFERENCE_JSON)

    logger.info("Conformance fixtures ready in %s", CONFORMANCE_DIR)
    logger.info("  reference.h5          — %d spectra", len(spectra))
    logger.info("  reference/parquet/    — catalog + per-category spectra")
    logger.info("  reference/json/       — catalog.json + spectra/")


if __name__ == "__main__":
    main()
