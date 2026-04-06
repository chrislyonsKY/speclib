# Format Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Formalize the speclib interchange format as a standalone, language-agnostic specification with a conformance test suite that Rust, R, and Python implementations can validate against.

**Architecture:** Extract the implicit schema from the Python HDF5/Parquet code into a Markdown spec document, build a small reference archive with representative spectra from each category, implement the JSON export (currently a stub), and write a validation script that checks any archive against the spec. The conformance suite lives in `tests/conformance/` and contains golden files + a Python validator.

**Tech Stack:** Python 3.11+, h5py, pyarrow, pytest, JSON schema

**Spec:** `docs/superpowers/specs/2026-04-06-ecostress-rust-r-design.md` (Section 1: Format Contract)

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `docs/format-spec.md` | Language-agnostic format specification |
| Create | `tests/conformance/build_reference.py` | Script to build reference archive from live data |
| Create | `tests/conformance/reference.h5` | Small HDF5 archive with 1 spectrum per category |
| Create | `tests/conformance/reference/catalog.parquet` | Expected Parquet catalog output |
| Create | `tests/conformance/reference/spectra/` | Expected per-category Parquet files |
| Create | `tests/conformance/reference/catalog.json` | Expected JSON catalog |
| Create | `tests/conformance/reference/spectra/` | Expected individual spectrum JSON files |
| Create | `tests/conformance/validate.py` | Validates any archive against the format spec |
| Create | `tests/test_conformance.py` | pytest wrapper around the validator |
| Modify | `src/speclib/export/json_export.py` | Implement JSON export (currently a stub) |
| Create | `tests/test_json_export.py` | Tests for JSON export |

---

### Task 1: Write the format specification document

Formalize the implicit schema from the Python code into a standalone Markdown spec. This is the authoritative reference for Rust and R implementers.

**Files:**
- Create: `docs/format-spec.md`

- [ ] **Step 1: Write the format spec**

Create `docs/format-spec.md` with the following content. This is derived from the actual HDF5 attribute structure in the live archive and the design spec:

```markdown
# speclib Format Specification v1.0

This document defines the interchange formats for speclib spectral archives.
Any compliant implementation (Python, Rust, R) MUST read and write data
conforming to this specification.

## 1. HDF5 Archive

The HDF5 archive is the source of truth. All other formats are derived from it.

### 1.1 File Structure

```
speclib_archive.h5
├── /metadata
│   ├── version           # scalar string: semver (e.g., "1.0.0")
│   ├── created           # scalar string: ISO 8601 timestamp
│   └── sources           # compound dataset: ingestion provenance
├── /{category}/
│   └── /{spectrum_id}/
│       ├── wavelengths   # float64 dataset, gzip-4, sorted ascending, µm
│       ├── reflectance   # float64 dataset, gzip-4, 0.0–1.0 scale
│       └── errors        # float64 dataset, gzip-4 (OPTIONAL)
└── ...
```

### 1.2 Category Groups

Top-level groups use the **lowercase enum value** of the material category:

| Group | MaterialCategory enum |
|-------|----------------------|
| `/mineral/` | MINERAL |
| `/rock/` | ROCK |
| `/soil/` | SOIL |
| `/vegetation/` | VEGETATION |
| `/vegetation_plot/` | VEGETATION_PLOT |
| `/water/` | WATER |
| `/manmade/` | MANMADE |
| `/mixture/` | MIXTURE |
| `/organic/` | ORGANIC |
| `/nonphotosynthetic_vegetation/` | NONPHOTOSYNTHETIC_VEGETATION |
| `/volatile/` | VOLATILE |
| `/ky_invasive/` | KY_INVASIVE |
| `/ky_mineral/` | KY_MINERAL |
| `/ky_reclamation/` | KY_RECLAMATION |

Groups are created on demand — empty categories have no group.

### 1.3 Spectrum Datasets

Each spectrum is an HDF5 group at `/{category}/{spectrum_id}/` containing:

| Dataset | dtype | Compression | Required | Constraints |
|---------|-------|-------------|----------|-------------|
| `wavelengths` | float64 | gzip level 4 | YES | Sorted ascending, micrometers (µm) |
| `reflectance` | float64 | gzip level 4 | YES | Nominally 0.0–1.0 (values outside range are flagged, not clipped) |
| `errors` | float64 | gzip level 4 | NO | Same length as wavelengths if present |

`wavelengths` and `reflectance` MUST have identical length.

### 1.4 Required Attributes

Every spectrum group MUST have these HDF5 attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Human-readable spectrum name |
| `spectrum_id` | string | Unique identifier: `{source}_{category}_{slug}_{hash8}` |
| `quality` | string | One of: VERIFIED, GOOD, FAIR, POOR, SUSPECT, DERIVED |
| `material_name` | string | Canonical material name |
| `material_category` | string | Enum value (see §1.2) |
| `source_library` | string | One of: USGS_SPLIB07, ECOSTRESS, ASTER_JPL, EMIT_L2B, KY_FIELD, CUSTOM |
| `source_record_id` | string | Original ID in upstream source |
| `measurement_type` | string | One of: LABORATORY, FIELD, AIRBORNE, SPACEBORNE, COMPUTED |
| `license` | string | Data license |
| `ingested_at` | string | ISO 8601 timestamp |
| `adapter_version` | string | Semver of the adapter that created this record |
| `source_filename` | string | Original filename from upstream source |

### 1.5 Optional Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `material_subcategory` | string | Subclass or finer classification |
| `formula` | string | Chemical formula or mineral class |
| `instrument` | string | Measurement instrument or method |
| `description` | string | Free-text description |
| `locality` | string | Collection locality |
| `citation` | string | Literature reference |
| `grain_size` | string | Grain size or particle size |
| `purity` | string | Sample purity assessment |
| `measurement_date` | string | ISO date of measurement |
| `geometry_wkt` | string | WKT geometry in EPSG:4326 (empty string if none) |
| `geometry_ky_wkt` | string | WKT geometry in EPSG:3089 (empty string if none) |
| `xrd_results` | string | XRD analysis results |
| `em_results` | string | Electron microscopy results |
| `extra` | string | JSON-encoded dict of additional key-value pairs |

Missing optional attributes SHOULD be stored as empty strings, not omitted.

### 1.6 Spectrum ID Generation

Deterministic: `{source}_{category}_{slug}_{hash8}`

- `source`: lowercase source_library value (e.g., `ecostress`)
- `category`: lowercase material_category value (e.g., `mineral`)
- `slug`: `name.lower().replace(" ", "_")[:40]`
- `hash8`: first 8 chars of `sha256(f"{source}:{category}:{name}:{source_filename}")`

### 1.7 Version Metadata

The `/metadata` group SHOULD contain:
- `version`: string, semver (current: `"1.0.0"`)
- `created`: string, ISO 8601 timestamp

Readers MUST check the major version and reject archives with incompatible versions.

## 2. Parquet Query Layer

Derived from HDF5. Regenerable. Uses snappy compression.

### 2.1 Catalog (`catalog.parquet`)

| Column | Arrow Type | Description |
|--------|-----------|-------------|
| `spectrum_id` | utf8 | Unique identifier |
| `name` | utf8 | Human-readable name |
| `material_category` | utf8 | Enum value |
| `source_library` | utf8 | Enum value |
| `quality` | utf8 | Quality flag enum value |
| `material_name` | utf8 | Canonical material name |
| `n_bands` | int64 | Number of spectral channels |
| `wavelength_min` | float64 | Minimum wavelength (µm) |
| `wavelength_max` | float64 | Maximum wavelength (µm) |
| `license` | utf8 | Data license |
| `citation` | utf8 | Literature reference |
| `instrument` | utf8 | Measurement instrument |
| `locality` | utf8 | Collection locality |

### 2.2 Spectra (`spectra/{category}.parquet`)

| Column | Arrow Type | Description |
|--------|-----------|-------------|
| `spectrum_id` | utf8 | Unique identifier |
| `name` | utf8 | Human-readable name |
| `wavelengths` | list\<float64\> | Wavelength array (µm) |
| `reflectance` | list\<float64\> | Reflectance array (0.0–1.0) |

Category filename uses the lowercase enum value (e.g., `mineral.parquet`).

### 2.3 GeoParquet Extension

Spectra with spatial provenance include:
- `geometry`: WKB-encoded, EPSG:4326
- `geometry_ky`: WKB-encoded, EPSG:3089 (Kentucky data only)

## 3. JSON Catalog (Static Web)

### 3.1 Catalog Index (`catalog.json`)

Array of objects with the same fields as the Parquet catalog (§2.1).

### 3.2 Individual Spectra (`spectra/{spectrum_id}.json`)

```json
{
  "spectrum_id": "ecostress_mineral_quartz_sio2_abc12345",
  "name": "Quartz SiO2",
  "wavelengths": [0.4, 0.41, ...],
  "reflectance": [0.05, 0.051, ...],
  "metadata": {
    "material_category": "MINERAL",
    "source_library": "ECOSTRESS",
    "quality": "GOOD",
    "material_name": "Quartz SiO2",
    "source_record_id": "S-2A",
    "measurement_type": "LABORATORY",
    "license": "CC0 / Public Domain",
    "description": "...",
    "locality": "...",
    "citation": "..."
  }
}
```

### 3.3 Taxonomy (`taxonomy.json`)

Nested tree of material categories:

```json
{
  "categories": [
    {"id": "MINERAL", "label": "Minerals", "children": []},
    {"id": "ROCK", "label": "Rocks", "children": []},
    ...
  ]
}
```

## 4. Enum Value Tables

### QualityFlag
VERIFIED, GOOD, FAIR, POOR, SUSPECT, DERIVED

### MaterialCategory
MINERAL, ROCK, SOIL, VEGETATION, VEGETATION_PLOT, WATER, MANMADE, MIXTURE, ORGANIC, NONPHOTOSYNTHETIC_VEGETATION, VOLATILE, KY_INVASIVE, KY_MINERAL, KY_RECLAMATION

### SourceLibrary
USGS_SPLIB07, ECOSTRESS, ASTER_JPL, EMIT_L2B, KY_FIELD, CUSTOM

### MeasurementType
LABORATORY, FIELD, AIRBORNE, SPACEBORNE, COMPUTED
```

- [ ] **Step 2: Commit**

```bash
git add docs/format-spec.md
git commit -m "Add language-agnostic format specification v1.0"
```

---

### Task 2: Implement JSON export

The JSON export is currently a stub. Implement `write()` and `batch_write()` to produce the format defined in §3 of the spec.

**Files:**
- Modify: `src/speclib/export/json_export.py`
- Create: `tests/test_json_export.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_json_export.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_json_export.py -v`
Expected: All FAIL with `NotImplementedError`.

- [ ] **Step 3: Implement JSON export**

Replace `src/speclib/export/json_export.py`:

```python
"""Export adapter: JSON format for static web viewer.

Produces individual spectrum JSON files and a catalog index
following the speclib format specification §3.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from speclib.core.spectrum import Spectrum

logger = logging.getLogger(__name__)


def write(spectrum: Spectrum, path: Path) -> None:
    """Write a single spectrum to JSON format.

    Args:
        spectrum: Spectrum to export.
        path: Output file path.
    """
    data = _spectrum_to_dict(spectrum)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def batch_write(spectra: list[Spectrum], path: Path) -> None:
    """Write catalog.json and individual spectrum files.

    Args:
        spectra: List of spectra to export.
        path: Output directory path.
    """
    path.mkdir(parents=True, exist_ok=True)
    spectra_dir = path / "spectra"
    spectra_dir.mkdir(exist_ok=True)

    catalog: list[dict] = []
    for spectrum in spectra:
        # Write individual spectrum file
        write(spectrum, spectra_dir / f"{spectrum.spectrum_id}.json")

        # Build catalog entry (metadata only, no arrays)
        catalog.append(
            {
                "spectrum_id": spectrum.spectrum_id,
                "name": spectrum.name,
                "material_category": spectrum.metadata.material_category.value,
                "source_library": spectrum.metadata.source_library.value,
                "quality": spectrum.quality.value,
                "material_name": spectrum.metadata.material_name,
                "n_bands": spectrum.n_bands,
                "wavelength_min": float(spectrum.wavelength_range[0]),
                "wavelength_max": float(spectrum.wavelength_range[1]),
                "license": spectrum.metadata.license,
                "citation": spectrum.metadata.citation,
                "instrument": spectrum.metadata.instrument,
                "locality": spectrum.metadata.locality,
                "measurement_type": spectrum.metadata.measurement_type.value,
            }
        )

    with (path / "catalog.json").open("w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    logger.info("Wrote catalog.json with %d entries and %d spectrum files", len(catalog), len(spectra))


def _spectrum_to_dict(spectrum: Spectrum) -> dict:
    """Convert a Spectrum to the JSON format defined in format-spec §3.2.

    Args:
        spectrum: Spectrum to serialize.

    Returns:
        Dictionary matching the JSON schema.
    """
    return {
        "spectrum_id": spectrum.spectrum_id,
        "name": spectrum.name,
        "wavelengths": spectrum.wavelengths.tolist(),
        "reflectance": spectrum.reflectance.tolist(),
        "metadata": {
            "material_category": spectrum.metadata.material_category.value,
            "source_library": spectrum.metadata.source_library.value,
            "quality": spectrum.quality.value,
            "material_name": spectrum.metadata.material_name,
            "source_record_id": spectrum.metadata.source_record_id,
            "measurement_type": spectrum.metadata.measurement_type.value,
            "license": spectrum.metadata.license,
            "description": spectrum.metadata.description,
            "locality": spectrum.metadata.locality,
            "citation": spectrum.metadata.citation,
        },
    }
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_json_export.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 5: Lint and commit**

```bash
ruff check src/speclib/export/json_export.py tests/test_json_export.py --fix
ruff format src/speclib/export/json_export.py tests/test_json_export.py
git add src/speclib/export/json_export.py tests/test_json_export.py
git commit -m "Implement JSON export for static web viewer"
```

---

### Task 3: Build the reference archive and conformance fixtures

Create a script that extracts a small representative sample (1 spectrum per category) from the live archive into a reference HDF5 file, then generates the expected Parquet and JSON outputs.

**Files:**
- Create: `tests/conformance/build_reference.py`

- [ ] **Step 1: Write the build script**

Create `tests/conformance/build_reference.py`:

```python
"""Build the conformance reference archive from the live speclib archive.

Extracts one representative spectrum per populated category, writes a
small reference HDF5, then generates expected Parquet and JSON outputs.

Usage:
    python tests/conformance/build_reference.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from speclib.core.spectrum import MaterialCategory
from speclib.export.json_export import batch_write
from speclib.storage.hdf5 import HDF5Archive
from speclib.storage.parquet import ParquetStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LIVE_ARCHIVE = project_root / "data" / "speclib_archive.h5"
CONFORMANCE_DIR = Path(__file__).parent
REFERENCE_HDF5 = CONFORMANCE_DIR / "reference.h5"
REFERENCE_PARQUET = CONFORMANCE_DIR / "reference" / "parquet"
REFERENCE_JSON = CONFORMANCE_DIR / "reference" / "json"


def main() -> None:
    """Build reference conformance fixtures."""
    if not LIVE_ARCHIVE.exists():
        logger.error("Live archive not found: %s", LIVE_ARCHIVE)
        sys.exit(1)

    live = HDF5Archive(LIVE_ARCHIVE)
    ref = HDF5Archive(REFERENCE_HDF5)

    # Delete old reference if it exists
    if REFERENCE_HDF5.exists():
        REFERENCE_HDF5.unlink()

    # Extract one spectrum per populated category
    spectra = []
    for cat in MaterialCategory:
        ids = live.list_ids(cat)
        if ids:
            spectrum = live.read(ids[0])
            ref.write(spectrum)
            spectra.append(spectrum)
            logger.info("Added %s: %s", cat.value, spectrum.name)

    logger.info("Reference archive: %d spectra from %d categories", len(spectra), len(spectra))

    # Generate expected Parquet output
    parquet = ParquetStore(REFERENCE_PARQUET)
    parquet.build_from_hdf5(ref)

    # Generate expected JSON output
    batch_write(spectra, REFERENCE_JSON)

    logger.info("Conformance fixtures built in %s", CONFORMANCE_DIR)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the build script**

```bash
python tests/conformance/build_reference.py
```

Expected: Creates `tests/conformance/reference.h5`, `tests/conformance/reference/parquet/`, and `tests/conformance/reference/json/`.

- [ ] **Step 3: Verify the outputs**

```python
from pathlib import Path
from speclib.storage.hdf5 import HDF5Archive

ref = HDF5Archive(Path("tests/conformance/reference.h5"))
ids = ref.list_ids()
print(f"Reference archive: {len(ids)} spectra")
for sid in ids:
    s = ref.read(sid)
    print(f"  {s.metadata.material_category.value}: {s.name}")
```

- [ ] **Step 4: Commit fixtures**

```bash
git add tests/conformance/
git commit -m "Add conformance reference archive and build script"
```

---

### Task 4: Write the format validator

A Python script that validates any HDF5 archive against the format spec. Returns structured pass/fail results. This is the contract enforcement tool.

**Files:**
- Create: `tests/conformance/validate.py`
- Create: `tests/test_conformance.py`

- [ ] **Step 1: Write failing conformance tests**

Create `tests/test_conformance.py`:

```python
"""Conformance tests: validate reference archive against format spec."""

from pathlib import Path

import pytest

from tests.conformance.validate import validate_hdf5, validate_parquet, validate_json

CONFORMANCE_DIR = Path(__file__).parent / "conformance"
REFERENCE_HDF5 = CONFORMANCE_DIR / "reference.h5"
REFERENCE_PARQUET = CONFORMANCE_DIR / "reference" / "parquet"
REFERENCE_JSON = CONFORMANCE_DIR / "reference" / "json"


@pytest.fixture
def reference_archive():
    """Path to the reference HDF5 archive."""
    if not REFERENCE_HDF5.exists():
        pytest.skip("Reference archive not built — run tests/conformance/build_reference.py")
    return REFERENCE_HDF5


@pytest.fixture
def reference_parquet():
    """Path to the reference Parquet directory."""
    if not REFERENCE_PARQUET.exists():
        pytest.skip("Reference Parquet not built")
    return REFERENCE_PARQUET


@pytest.fixture
def reference_json():
    """Path to the reference JSON directory."""
    if not REFERENCE_JSON.exists():
        pytest.skip("Reference JSON not built")
    return REFERENCE_JSON


class TestHDF5Conformance:
    """Validate HDF5 archive against format spec."""

    def test_all_spectra_have_required_attributes(self, reference_archive):
        """Every spectrum group has all required attributes."""
        errors = validate_hdf5(reference_archive)
        attr_errors = [e for e in errors if "missing required attribute" in e]
        assert attr_errors == [], f"Missing attributes:\n" + "\n".join(attr_errors)

    def test_wavelengths_ascending(self, reference_archive):
        """All wavelength datasets are sorted ascending."""
        errors = validate_hdf5(reference_archive)
        wl_errors = [e for e in errors if "wavelengths not ascending" in e]
        assert wl_errors == [], f"Wavelength errors:\n" + "\n".join(wl_errors)

    def test_datasets_same_length(self, reference_archive):
        """wavelengths and reflectance have matching lengths."""
        errors = validate_hdf5(reference_archive)
        len_errors = [e for e in errors if "length mismatch" in e]
        assert len_errors == [], f"Length errors:\n" + "\n".join(len_errors)

    def test_enum_values_valid(self, reference_archive):
        """All enum attributes contain valid values."""
        errors = validate_hdf5(reference_archive)
        enum_errors = [e for e in errors if "invalid enum value" in e]
        assert enum_errors == [], f"Enum errors:\n" + "\n".join(enum_errors)

    def test_no_errors(self, reference_archive):
        """Full validation passes with zero errors."""
        errors = validate_hdf5(reference_archive)
        assert errors == [], f"Validation errors:\n" + "\n".join(errors)


class TestParquetConformance:
    """Validate Parquet files against format spec."""

    def test_catalog_has_required_columns(self, reference_parquet):
        """catalog.parquet contains all required columns."""
        errors = validate_parquet(reference_parquet)
        col_errors = [e for e in errors if "missing column" in e]
        assert col_errors == [], f"Missing columns:\n" + "\n".join(col_errors)

    def test_no_errors(self, reference_parquet):
        """Full Parquet validation passes."""
        errors = validate_parquet(reference_parquet)
        assert errors == [], f"Validation errors:\n" + "\n".join(errors)


class TestJsonConformance:
    """Validate JSON files against format spec."""

    def test_catalog_is_array(self, reference_json):
        """catalog.json is a JSON array."""
        errors = validate_json(reference_json)
        array_errors = [e for e in errors if "catalog.json" in e and "array" in e]
        assert array_errors == []

    def test_spectrum_files_have_required_fields(self, reference_json):
        """Individual spectrum JSON files have required fields."""
        errors = validate_json(reference_json)
        field_errors = [e for e in errors if "missing field" in e]
        assert field_errors == [], f"Missing fields:\n" + "\n".join(field_errors)

    def test_no_errors(self, reference_json):
        """Full JSON validation passes."""
        errors = validate_json(reference_json)
        assert errors == [], f"Validation errors:\n" + "\n".join(errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_conformance.py -v`
Expected: FAIL — `validate` module doesn't exist.

- [ ] **Step 3: Implement the validator**

Create `tests/conformance/__init__.py` (empty) and `tests/conformance/validate.py`:

```python
"""Format spec validator for speclib archives.

Validates HDF5, Parquet, and JSON outputs against the format spec.
Returns a list of error strings (empty = conformant).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import h5py
import numpy as np
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

REQUIRED_ATTRS = [
    "name",
    "spectrum_id",
    "quality",
    "material_name",
    "material_category",
    "source_library",
    "source_record_id",
    "measurement_type",
    "license",
    "ingested_at",
    "adapter_version",
    "source_filename",
]

VALID_QUALITY = {"VERIFIED", "GOOD", "FAIR", "POOR", "SUSPECT", "DERIVED"}

VALID_CATEGORY = {
    "MINERAL", "ROCK", "SOIL", "VEGETATION", "VEGETATION_PLOT",
    "WATER", "MANMADE", "MIXTURE", "ORGANIC",
    "NONPHOTOSYNTHETIC_VEGETATION", "VOLATILE",
    "KY_INVASIVE", "KY_MINERAL", "KY_RECLAMATION",
}

VALID_SOURCE = {
    "USGS_SPLIB07", "ECOSTRESS", "ASTER_JPL", "EMIT_L2B", "KY_FIELD", "CUSTOM",
}

VALID_MEASUREMENT = {"LABORATORY", "FIELD", "AIRBORNE", "SPACEBORNE", "COMPUTED"}

CATALOG_COLUMNS = {
    "spectrum_id", "name", "material_category", "source_library",
    "quality", "material_name", "n_bands", "wavelength_min",
    "wavelength_max", "license", "citation", "instrument", "locality",
}

JSON_REQUIRED_FIELDS = {"spectrum_id", "name", "wavelengths", "reflectance", "metadata"}


def validate_hdf5(path: Path) -> list[str]:
    """Validate an HDF5 archive against the format spec.

    Args:
        path: Path to the HDF5 file.

    Returns:
        List of error strings. Empty means fully conformant.
    """
    errors: list[str] = []

    with h5py.File(path, "r") as f:
        for cat_name in f:
            if cat_name == "metadata":
                continue
            if not isinstance(f[cat_name], h5py.Group):
                continue

            for spectrum_id in f[cat_name]:
                grp = f[cat_name][spectrum_id]
                prefix = f"/{cat_name}/{spectrum_id}"

                # Check required datasets
                if "wavelengths" not in grp:
                    errors.append(f"{prefix}: missing required dataset 'wavelengths'")
                    continue
                if "reflectance" not in grp:
                    errors.append(f"{prefix}: missing required dataset 'reflectance'")
                    continue

                wl = np.array(grp["wavelengths"])
                refl = np.array(grp["reflectance"])

                # Length match
                if len(wl) != len(refl):
                    errors.append(
                        f"{prefix}: length mismatch — wavelengths={len(wl)}, reflectance={len(refl)}"
                    )

                # Ascending wavelengths
                if len(wl) > 1 and not np.all(np.diff(wl) >= 0):
                    errors.append(f"{prefix}: wavelengths not ascending")

                # Errors dataset length
                if "errors" in grp:
                    err_data = np.array(grp["errors"])
                    if len(err_data) != len(wl):
                        errors.append(
                            f"{prefix}: errors length mismatch — errors={len(err_data)}, wavelengths={len(wl)}"
                        )

                # Required attributes
                for attr in REQUIRED_ATTRS:
                    if attr not in grp.attrs:
                        errors.append(f"{prefix}: missing required attribute '{attr}'")

                # Enum validation
                quality = str(grp.attrs.get("quality", ""))
                if quality and quality not in VALID_QUALITY:
                    errors.append(f"{prefix}: invalid enum value quality='{quality}'")

                category = str(grp.attrs.get("material_category", ""))
                if category and category not in VALID_CATEGORY:
                    errors.append(f"{prefix}: invalid enum value material_category='{category}'")

                source = str(grp.attrs.get("source_library", ""))
                if source and source not in VALID_SOURCE:
                    errors.append(f"{prefix}: invalid enum value source_library='{source}'")

                mtype = str(grp.attrs.get("measurement_type", ""))
                if mtype and mtype not in VALID_MEASUREMENT:
                    errors.append(f"{prefix}: invalid enum value measurement_type='{mtype}'")

    return errors


def validate_parquet(path: Path) -> list[str]:
    """Validate Parquet query layer against the format spec.

    Args:
        path: Path to the Parquet directory.

    Returns:
        List of error strings.
    """
    errors: list[str] = []

    catalog_path = path / "catalog.parquet"
    if not catalog_path.exists():
        errors.append("catalog.parquet not found")
        return errors

    table = pq.read_table(catalog_path)
    actual_columns = set(table.column_names)

    for col in CATALOG_COLUMNS:
        if col not in actual_columns:
            errors.append(f"catalog.parquet: missing column '{col}'")

    # Check spectra directory
    spectra_dir = path / "spectra"
    if spectra_dir.exists():
        for pq_file in spectra_dir.glob("*.parquet"):
            t = pq.read_table(pq_file)
            cols = set(t.column_names)
            for required in ("spectrum_id", "name", "wavelengths", "reflectance"):
                if required not in cols:
                    errors.append(f"spectra/{pq_file.name}: missing column '{required}'")

    return errors


def validate_json(path: Path) -> list[str]:
    """Validate JSON catalog and spectrum files against the format spec.

    Args:
        path: Path to the JSON directory.

    Returns:
        List of error strings.
    """
    errors: list[str] = []

    catalog_path = path / "catalog.json"
    if not catalog_path.exists():
        errors.append("catalog.json not found")
        return errors

    with catalog_path.open() as f:
        catalog = json.load(f)

    if not isinstance(catalog, list):
        errors.append("catalog.json: expected JSON array, got " + type(catalog).__name__)
        return errors

    # Check individual spectrum files
    spectra_dir = path / "spectra"
    if spectra_dir.exists():
        for json_file in spectra_dir.glob("*.json"):
            with json_file.open() as f:
                data = json.load(f)
            for field in JSON_REQUIRED_FIELDS:
                if field not in data:
                    errors.append(f"spectra/{json_file.name}: missing field '{field}'")

    return errors
```

- [ ] **Step 4: Create `__init__.py` for the conformance package**

Create empty `tests/conformance/__init__.py`:

```python
```

- [ ] **Step 5: Run conformance tests**

Run: `pytest tests/test_conformance.py -v`
Expected: All 8 tests PASS (if reference archive was built in Task 3).

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 7: Lint and commit**

```bash
ruff check tests/conformance/ tests/test_conformance.py --fix
ruff format tests/conformance/ tests/test_conformance.py
git add tests/conformance/validate.py tests/conformance/__init__.py tests/test_conformance.py
git commit -m "Add format validator and conformance test suite"
```

---

### Task 5: Add version metadata to HDF5 archive

The format spec requires a `/metadata` group with `version` and `created`. Update `HDF5Archive` to write this on archive creation.

**Files:**
- Modify: `src/speclib/storage/hdf5.py`
- Modify: `tests/test_hdf5.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_hdf5.py`:

```python
import h5py


class TestHDF5Metadata:
    """Tests for archive-level metadata."""

    def test_write_creates_metadata_group(self):
        """Writing a spectrum creates /metadata group with version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test.h5")
            archive.write(_make_spectrum())

            with h5py.File(archive.path, "r") as f:
                assert "metadata" in f
                assert "version" in f["metadata"].attrs
                assert f["metadata"].attrs["version"] == "1.0.0"

    def test_metadata_has_created_timestamp(self):
        """Archive metadata includes created timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test.h5")
            archive.write(_make_spectrum())

            with h5py.File(archive.path, "r") as f:
                assert "created" in f["metadata"].attrs
                # Should be ISO 8601
                created = f["metadata"].attrs["created"]
                assert "T" in created or "-" in created
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hdf5.py::TestHDF5Metadata -v`
Expected: FAIL — no `/metadata` group.

- [ ] **Step 3: Update HDF5Archive.write() to create metadata**

In `src/speclib/storage/hdf5.py`, add to the `write()` method, at the start of the `with h5py.File(...)` block before creating the spectrum group:

```python
# Ensure /metadata group exists
if "metadata" not in f:
    meta_grp = f.create_group("metadata")
    meta_grp.attrs["version"] = "1.0.0"
    meta_grp.attrs["created"] = datetime.now(UTC).isoformat()
```

Add this import at the top of the file:

```python
from datetime import UTC, datetime
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_hdf5.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Update `list_ids` to skip metadata group**

The `list_ids()` method iterates top-level groups — it should skip `/metadata`. Check if it already does (it checks `isinstance(f[cat_name], h5py.Group)` and then looks for spectrum children — metadata has none so it should be harmless, but add an explicit skip for clarity):

In the `list_ids` method, after `categories = [category.value.lower()] if category else list(f.keys())`, add:

```python
categories = [c for c in categories if c != "metadata"]
```

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 7: Lint and commit**

```bash
ruff check src/speclib/storage/hdf5.py tests/test_hdf5.py --fix
ruff format src/speclib/storage/hdf5.py tests/test_hdf5.py
git add src/speclib/storage/hdf5.py tests/test_hdf5.py
git commit -m "Add /metadata group with version and created to HDF5 archive"
```

---

## Follow-Up (not part of this plan)

- Rebuild the reference archive after Task 5 to include `/metadata` group: `python tests/conformance/build_reference.py`
- Recommit the updated reference fixtures
