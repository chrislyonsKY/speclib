# ECOSTRESS Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the ECOSTRESS adapter's broken header parser and ingest 3,311 spectra from the ECOSTRESS spectral library download into speclib's HDF5 archive.

**Architecture:** The existing `EcostressAdapter` in `src/speclib/ingest/ecostress.py` has a positional header parser that doesn't actually extract values from the `Key: Value` format used in ECOSTRESS files. We rewrite the parser to handle key-value headers dynamically, add ancillary file linking, handle descending wavelengths, and add the `NONPHOTOSYNTHETIC_VEGETATION` material category. All changes are test-driven against real sample files extracted from the ECOSTRESS zip.

**Tech Stack:** Python 3.11+, numpy, h5py, pytest, ruff

**Spec:** `docs/superpowers/specs/2026-04-06-ecostress-rust-r-design.md` (Phase 1)

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `tests/data/ecostress/` | Sample ECOSTRESS files for testing |
| Create | `tests/test_ecostress_adapter.py` | ECOSTRESS adapter unit + integration tests |
| Modify | `src/speclib/core/spectrum.py:33-48` | Add `NONPHOTOSYNTHETIC_VEGETATION` to `MaterialCategory` |
| Modify | `src/speclib/ingest/ecostress.py` | Rewrite header parser, ancillary linking, wavelength sort |
| Modify | `data/upstream/ecostress.yaml` | Set `data_dir` to extracted ECOSTRESS path |
| Modify | `tests/test_spectrum.py` | Update enum test for new category |

---

### Task 1: Create test sample files

Extract a small representative set of ECOSTRESS files from the zip for use as test fixtures. We need one spectrum + ancillary pair per material type to cover header field variations.

**Files:**
- Create: `tests/data/ecostress/mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt`
- Create: `tests/data/ecostress/mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.ancillary.txt`
- Create: `tests/data/ecostress/vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt`
- Create: `tests/data/ecostress/vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.ancillary.txt` (if exists)
- Create: `tests/data/ecostress/nonphotosyntheticvegetation.bark.pinus.coulteri.vswir.vh342.ucsb.asd.spectrum.txt`
- Create: `tests/data/ecostress/soil.alfisol.fragiboralf.none.all.86p1994.jhu.becknic.spectrum.txt`

- [ ] **Step 1: Create the test data directory**

```bash
mkdir -p tests/data/ecostress
```

- [ ] **Step 2: Extract sample files from the zip**

```python
# Run from project root:
# python scripts/extract_test_samples.py
# Or manually via:
import zipfile
from pathlib import Path

samples = [
    "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt",
    "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.ancillary.txt",
    "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt",
    "nonphotosyntheticvegetation.bark.pinus.coulteri.vswir.vh342.ucsb.asd.spectrum.txt",
    "soil.alfisol.fragiboralf.none.all.86p1994.jhu.becknic.spectrum.txt",
    "soil.alfisol.fragiboralf.none.all.86p1994.jhu.becknic.ancillary.txt",
]

z = zipfile.ZipFile(r"C:\Users\chris.lyons\Downloads\ecospeclib-1775149306367.zip")
out = Path("tests/data/ecostress")
for name in samples:
    if name in z.namelist():
        data = z.read(name)
        (out / name).write_bytes(data)
        print(f"Extracted: {name} ({len(data)} bytes)")
    else:
        print(f"NOT FOUND: {name}")
```

Note: The vegetation grass sample may not have a paired ancillary file. That's OK — it tests the no-ancillary path.

- [ ] **Step 3: Verify extracted files have expected headers**

```bash
head -20 tests/data/ecostress/mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt
head -20 tests/data/ecostress/vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt
head -20 tests/data/ecostress/nonphotosyntheticvegetation.bark.pinus.coulteri.vswir.vh342.ucsb.asd.spectrum.txt
```

Expected: Each file starts with `Name:` line followed by key-value header pairs.

- [ ] **Step 4: Commit test fixtures**

```bash
git add tests/data/ecostress/
git commit -m "Add ECOSTRESS sample files for adapter testing"
```

---

### Task 2: Add NONPHOTOSYNTHETIC_VEGETATION to MaterialCategory

The ECOSTRESS data includes a `non photosynthetic vegetation` type (note: spaces in the Type field, no spaces in the filename prefix). The `MaterialCategory` enum needs a new member.

**Files:**
- Modify: `src/speclib/core/spectrum.py:33-48` (MaterialCategory enum)
- Modify: `tests/test_spectrum.py:42-49` (TestMaterialCategory)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_spectrum.py` inside `TestMaterialCategory`:

```python
def test_nonphotosynthetic_vegetation_category(self):
    """Non-photosynthetic vegetation category is defined."""
    assert MaterialCategory.NONPHOTOSYNTHETIC_VEGETATION.value == "NONPHOTOSYNTHETIC_VEGETATION"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_spectrum.py::TestMaterialCategory::test_nonphotosynthetic_vegetation_category -v`
Expected: FAIL with `AttributeError: 'NONPHOTOSYNTHETIC_VEGETATION' is not a member of 'MaterialCategory'`

- [ ] **Step 3: Add the new enum member**

In `src/speclib/core/spectrum.py`, add after the `ORGANIC = "ORGANIC"` line (line 44) and before `VOLATILE`:

```python
NONPHOTOSYNTHETIC_VEGETATION = "NONPHOTOSYNTHETIC_VEGETATION"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_spectrum.py::TestMaterialCategory -v`
Expected: All `TestMaterialCategory` tests PASS.

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `pytest tests/ -v`
Expected: All 16 tests PASS (15 existing + 1 new).

- [ ] **Step 6: Commit**

```bash
git add src/speclib/core/spectrum.py tests/test_spectrum.py
git commit -m "Add NONPHOTOSYNTHETIC_VEGETATION to MaterialCategory enum"
```

---

### Task 3: Rewrite ECOSTRESS header parser

The current `_read_header()` uses positional indexing and stores raw lines like `"Name: Avena fatua"` as values. Rewrite to parse `Key: Value` format and handle variable fields across material types (minerals have Subclass/Particle Size; vegetation has Genus/Species; NPV Type field is `"non photosynthetic vegetation"` with spaces).

**Files:**
- Create: `tests/test_ecostress_adapter.py`
- Modify: `src/speclib/ingest/ecostress.py:29-53, 217-234` (header fields list and `_read_header`)

- [ ] **Step 1: Write failing tests for header parsing**

Create `tests/test_ecostress_adapter.py`:

```python
"""Tests for ECOSTRESS/ASTER spectral library ingestion adapter."""

from pathlib import Path

import numpy as np
import pytest

from speclib.ingest.ecostress import _read_header

ECOSTRESS_DATA = Path(__file__).parent / "data" / "ecostress"


class TestReadHeader:
    """Tests for the _read_header function."""

    def test_mineral_header_extracts_values(self):
        """Mineral spectrum header values are extracted without key prefixes."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        header = _read_header(path)
        # Value should be "Hematite alpha Fe_2O_3", NOT "Name: Hematite alpha Fe_2O_3"
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
        path = ECOSTRESS_DATA / "nonphotosyntheticvegetation.bark.pinus.coulteri.vswir.vh342.ucsb.asd.spectrum.txt"
        header = _read_header(path)
        assert header["Type"] == "non photosynthetic vegetation"
        assert header["Genus"] == "Pinus"
        assert header["Species"] == "coulteri"

    def test_header_extracts_wavelength_unit(self):
        """X Units field is parsed from the header."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        header = _read_header(path)
        assert "micrometers" in header["X Units"].lower() or "micrometer" in header["X Units"].lower()

    def test_header_extracts_data_unit(self):
        """Y Units field is parsed from the header."""
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        header = _read_header(path)
        assert "percentage" in header["Y Units"].lower() or "percent" in header["Y Units"].lower()

    def test_header_stops_at_additional_info(self):
        """Header parsing stops at the Additional Information line."""
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        header = _read_header(path)
        assert "Additional Information" in header
        # Should not contain spectral data values
        for value in header.values():
            # No value should be a pure float (data line)
            try:
                float(value)
                # If it's a header value like "0.35" for First X Value, that's OK
                # But it should have a key
            except ValueError:
                pass  # Expected for text values
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ecostress_adapter.py::TestReadHeader -v`
Expected: Most tests FAIL because `_read_header` returns raw lines with key prefixes.

- [ ] **Step 3: Rewrite `_read_header` to parse key-value format**

Replace the `_HEADER_FIELDS` list and `_read_header` function in `src/speclib/ingest/ecostress.py`.

Remove lines 29-53 (the `_HEADER_FIELDS` list). Replace the `_read_header` function (lines 217-234) with:

```python
def _read_header(path: Path) -> dict[str, str]:
    """Read the structured header from an ECOSTRESS/ASTER spectrum file.

    Parses key-value pairs separated by the first colon on each line.
    Header ends at the blank line following the last header field.

    Args:
        path: Path to the .spectrum.txt or .ancillary.txt file.

    Returns:
        Dictionary mapping header field names to their values.
    """
    header: dict[str, str] = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                break
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                header[key.strip()] = value.strip()
            else:
                # Lines without colons after the first line signal end of header
                if header:
                    break
    return header
```

- [ ] **Step 4: Update references to `_HEADER_FIELDS` in `fetch()`**

The `fetch()` method at line 130 uses `data_start = min(len(_HEADER_FIELDS), len(lines))`. Replace the data start detection in `fetch()` with blank-line detection:

```python
def fetch(self, record_id: str) -> RawSpectrum:
    """Read a single .spectrum.txt file.

    Args:
        record_id: Absolute path to the spectrum file.

    Returns:
        RawSpectrum with wavelengths and reflectance in source units.
    """
    txt_path = Path(record_id)
    header = _read_header(txt_path)

    wavelengths: list[float] = []
    values: list[float] = []

    with txt_path.open(encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Find data start: first line after a blank line that follows header
    data_start = 0
    in_header = True
    for i, line in enumerate(lines):
        if in_header:
            if not line.strip():
                in_header = False
        else:
            data_start = i
            break

    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            parts = line.split(",")
        if len(parts) < 2:
            continue
        try:
            wl = float(parts[0])
            val = float(parts[1])
            wavelengths.append(wl)
            values.append(val)
        except ValueError:
            continue

    wl_unit = header.get("X Units", "").lower()
    data_unit = header.get("Y Units", "").lower()

    refl_scale = "percent" if "percent" in data_unit else "fractional"

    return RawSpectrum(
        record_id=record_id,
        wavelengths=np.array(wavelengths),
        reflectance=np.array(values),
        wavelength_unit="um" if "micro" in wl_unit else wl_unit,
        reflectance_scale=refl_scale,
        metadata=header,
    )
```

- [ ] **Step 5: Run header tests to verify they pass**

Run: `pytest tests/test_ecostress_adapter.py::TestReadHeader -v`
Expected: All 6 tests PASS.

- [ ] **Step 6: Lint and commit**

```bash
ruff check src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py --fix
ruff format src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git add src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git commit -m "Rewrite ECOSTRESS header parser to handle key-value format"
```

---

### Task 4: Add descending wavelength sort to normalize()

Some ECOSTRESS spectra (minerals, soils, rocks from ASTER/JPL origin) have wavelengths in descending order. The `normalize()` method must detect this and sort both arrays ascending.

**Files:**
- Modify: `tests/test_ecostress_adapter.py` (add fetch + normalize tests)
- Modify: `src/speclib/ingest/ecostress.py` (normalize method)

- [ ] **Step 1: Write failing test for descending wavelength handling**

Add to `tests/test_ecostress_adapter.py`:

```python
import tempfile

import yaml

from speclib.ingest.ecostress import EcostressAdapter


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


class TestFetchAndNormalize:
    """Tests for fetch() and normalize() pipeline."""

    def test_mineral_descending_wavelengths_sorted_ascending(self):
        """Mineral spectra with descending wavelengths are sorted ascending after normalize."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        raw = adapter.fetch(str(path))
        # Raw data should be descending (source order)
        assert raw.wavelengths[0] > raw.wavelengths[-1], "Expected descending raw wavelengths"
        spectrum = adapter.normalize(raw)
        # Normalized must be ascending
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
        # Original data has values like 4.474 (percent) -> 0.04474
        assert np.all(spectrum.reflectance <= 1.0)
        assert np.all(spectrum.reflectance >= 0.0) or np.any(np.isnan(spectrum.reflectance))
```

- [ ] **Step 2: Run tests to verify the descending wavelength test fails**

Run: `pytest tests/test_ecostress_adapter.py::TestFetchAndNormalize -v`
Expected: `test_mineral_descending_wavelengths_sorted_ascending` FAILS because `normalize()` doesn't sort.

- [ ] **Step 3: Add wavelength sort to normalize()**

In `src/speclib/ingest/ecostress.py`, in the `normalize()` method, add after the wavelength unit conversion block (after `wavelengths = wavelengths / 1000.0`) and before the reflectance conversion:

```python
# Sort ascending if wavelengths are descending
if len(wavelengths) > 1 and wavelengths[0] > wavelengths[-1]:
    sort_idx = np.argsort(wavelengths)
    wavelengths = wavelengths[sort_idx]
    reflectance = reflectance[sort_idx]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ecostress_adapter.py::TestFetchAndNormalize -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
ruff check src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py --fix
ruff format src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git add src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git commit -m "Sort descending ECOSTRESS wavelengths ascending in normalize()"
```

---

### Task 5: Update normalize() for new header keys and NPV category

The `normalize()` method references old header keys (e.g., `header.get("WavelengthUnit")`) that no longer exist after the parser rewrite. Update it to use the actual parsed keys (`X Units`, `Y Units`, etc.) and add the NPV type mapping.

**Files:**
- Modify: `tests/test_ecostress_adapter.py` (add NPV and metadata tests)
- Modify: `src/speclib/ingest/ecostress.py` (normalize method + type map)

- [ ] **Step 1: Write failing tests for NPV category and metadata extraction**

Add to `tests/test_ecostress_adapter.py` inside `TestFetchAndNormalize`:

```python
    def test_npv_maps_to_correct_category(self):
        """Non-photosynthetic vegetation maps to NONPHOTOSYNTHETIC_VEGETATION category."""
        from speclib.core.spectrum import MaterialCategory

        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "nonphotosyntheticvegetation.bark.pinus.coulteri.vswir.vh342.ucsb.asd.spectrum.txt"
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
```

- [ ] **Step 2: Run tests to verify NPV test fails**

Run: `pytest tests/test_ecostress_adapter.py::TestFetchAndNormalize::test_npv_maps_to_correct_category -v`
Expected: FAIL — `"non photosynthetic vegetation"` not in `_TYPE_MAP`.

- [ ] **Step 3: Update `_TYPE_MAP` and `normalize()`**

In `src/speclib/ingest/ecostress.py`, update the `_TYPE_MAP` dict:

```python
_TYPE_MAP: dict[str, str] = {
    "mineral": "MINERAL",
    "rock": "ROCK",
    "soil": "SOIL",
    "vegetation": "VEGETATION",
    "non photosynthetic vegetation": "NONPHOTOSYNTHETIC_VEGETATION",
    "water": "WATER",
    "manmade": "MANMADE",
    "mixture": "MIXTURE",
    "organic": "ORGANIC",
}
```

Update the `normalize()` method to use the new parsed header keys. Replace the full `normalize()` method with:

```python
def normalize(self, raw: RawSpectrum) -> Spectrum:
    """Convert ECOSTRESS/ASTER raw data to normalized Spectrum.

    Args:
        raw: RawSpectrum from fetch().

    Returns:
        Normalized Spectrum with wavelength in um and reflectance 0-1.
    """
    wavelengths = raw.wavelengths.copy()
    reflectance = raw.reflectance.copy()

    # Convert nm to um if needed
    if raw.wavelength_unit == "nm" or (len(wavelengths) > 0 and wavelengths[0] > 100):
        wavelengths = wavelengths / 1000.0

    # Sort ascending if wavelengths are descending
    if len(wavelengths) > 1 and wavelengths[0] > wavelengths[-1]:
        sort_idx = np.argsort(wavelengths)
        wavelengths = wavelengths[sort_idx]
        reflectance = reflectance[sort_idx]

    # Convert percentage to fractional
    if raw.reflectance_scale == "percent":
        reflectance = reflectance / 100.0

    header = raw.metadata
    source = self.config.get("source", "ECOSTRESS")
    source_lib = SourceLibrary.ECOSTRESS if source == "ECOSTRESS" else SourceLibrary.ASTER_JPL

    type_str = header.get("Type", "").lower()
    category_str = _TYPE_MAP.get(type_str, "MINERAL")
    category = MaterialCategory(category_str)

    name = header.get("Name", Path(raw.record_id).stem)

    metadata = SampleMetadata(
        material_name=name,
        material_category=category,
        source_library=source_lib,
        source_record_id=header.get("Sample No.", Path(raw.record_id).stem),
        measurement_type=MeasurementType.LABORATORY,
        license=self.config.get("license", "CC0 / Public Domain"),
        material_subcategory=header.get("Subclass", header.get("Class", "")),
        formula=header.get("Class", ""),
        instrument=header.get("Measurement", ""),
        description=header.get("Description", ""),
        locality=header.get("Origin", ""),
        citation=self.config.get("citation", ""),
        source_filename=Path(raw.record_id).name,
    )

    # Store genus/species in extra if present
    extra: dict[str, str] = {}
    if header.get("Genus"):
        extra["genus"] = header["Genus"]
    if header.get("Species"):
        extra["species"] = header["Species"]
    if header.get("Particle Size"):
        extra["particle_size"] = header["Particle Size"]
    if header.get("Wavelength Range"):
        extra["wavelength_range"] = header["Wavelength Range"]
    if header.get("Owner"):
        extra["owner"] = header["Owner"]
    if header.get("Collection Date"):
        extra["collection_date"] = header["Collection Date"]
    if extra:
        metadata.extra = extra

    return Spectrum(
        name=name,
        wavelengths=wavelengths,
        reflectance=reflectance,
        metadata=metadata,
        quality=QualityFlag.GOOD,
    )
```

- [ ] **Step 4: Run all adapter tests**

Run: `pytest tests/test_ecostress_adapter.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS (no regressions).

- [ ] **Step 6: Lint and commit**

```bash
ruff check src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py --fix
ruff format src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git add src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git commit -m "Update normalize() for parsed header keys and NPV category"
```

---

### Task 6: Add ancillary file linking

Ancillary files (`.ancillary.txt`) contain chemistry, biophysical properties, and literature references. The adapter should discover paired ancillary files and merge their metadata. Ancillary files have the same key-value header as spectrum files, plus freeform content below (chemistry data, XRD results, etc.).

**Files:**
- Modify: `tests/test_ecostress_adapter.py` (add ancillary tests)
- Modify: `src/speclib/ingest/ecostress.py` (add `_read_ancillary`, update `normalize`)

- [ ] **Step 1: Write failing tests for ancillary linking**

Add to `tests/test_ecostress_adapter.py`:

```python
from speclib.ingest.ecostress import _read_ancillary


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
        # Mineral ancillary files typically have XRD analysis
        assert "ancillary_text" in anc

    def test_normalize_merges_ancillary_when_present(self):
        """Ancillary metadata is merged into the spectrum's extra dict."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.spectrum.txt"
        raw = adapter.fetch(str(path))
        spectrum = adapter.normalize(raw)
        # The mineral ancillary file should exist alongside the spectrum
        anc_path = ECOSTRESS_DATA / "mineral.oxide.none.fine.vswir.o-1b.jpl.perkin.ancillary.txt"
        if anc_path.exists():
            assert "ancillary_text" in spectrum.metadata.extra

    def test_normalize_works_without_ancillary(self):
        """Spectra without paired ancillary files normalize successfully."""
        adapter = _make_adapter()
        path = ECOSTRESS_DATA / "vegetation.grass.avena.fatua.vswir.vh353.ucsb.asd.spectrum.txt"
        raw = adapter.fetch(str(path))
        # Should not raise
        spectrum = adapter.normalize(raw)
        assert spectrum.name == "Avena fatua"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_ecostress_adapter.py::TestAncillaryLinking -v`
Expected: FAIL — `_read_ancillary` does not exist.

- [ ] **Step 3: Implement `_read_ancillary` function**

Add to `src/speclib/ingest/ecostress.py` below `_read_header`:

```python
def _read_ancillary(path: Path) -> dict[str, str]:
    """Read an ECOSTRESS/ASTER ancillary metadata file.

    Ancillary files have the same key-value header as spectrum files,
    followed by freeform text containing chemistry, XRD analysis, etc.

    Args:
        path: Path to the .ancillary.txt file.

    Returns:
        Dictionary with parsed header fields plus 'ancillary_text'
        containing any freeform content below the header.
    """
    result = _read_header(path)

    # Read remaining freeform content after the header
    lines: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    # Find where header ends (first blank line)
    body_start = 0
    for i, line in enumerate(all_lines):
        if not line.strip():
            body_start = i + 1
            break

    freeform = "".join(all_lines[body_start:]).strip()
    if freeform:
        result["ancillary_text"] = freeform

    return result
```

- [ ] **Step 4: Update `normalize()` to link ancillary files**

In the `normalize()` method, add ancillary linking after the `extra` dict is populated and before the `if extra:` check. Insert:

```python
# Link paired ancillary file if it exists
ancillary_path = Path(raw.record_id).with_suffix("").with_suffix("")  # strip .spectrum.txt
ancillary_name = Path(raw.record_id).name.replace(".spectrum.txt", ".ancillary.txt")
ancillary_file = Path(raw.record_id).parent / ancillary_name
if ancillary_file.exists():
    try:
        anc_data = _read_ancillary(ancillary_file)
        if "ancillary_text" in anc_data:
            extra["ancillary_text"] = anc_data["ancillary_text"]
        # Merge known ancillary fields
        if anc_data.get("Chemistry"):
            extra["chemistry"] = anc_data["Chemistry"]
        if anc_data.get("Biophysical Properties"):
            extra["biophysical_properties"] = anc_data["Biophysical Properties"]
        if anc_data.get("Reference"):
            citation = self.config.get("citation", "")
            ref = anc_data["Reference"]
            metadata.citation = f"{citation}; {ref}" if citation else ref
    except Exception:
        logger.warning("Failed to read ancillary file: %s", ancillary_file)
```

- [ ] **Step 5: Run ancillary tests**

Run: `pytest tests/test_ecostress_adapter.py::TestAncillaryLinking -v`
Expected: All 4 tests PASS.

- [ ] **Step 6: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 7: Lint and commit**

```bash
ruff check src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py --fix
ruff format src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git add src/speclib/ingest/ecostress.py tests/test_ecostress_adapter.py
git commit -m "Add ancillary file linking to ECOSTRESS adapter"
```

---

### Task 7: Update discover() for new header parser

The `discover()` method also calls `_read_header` and reads `header.get("Type")` — it now gets correct values thanks to the parser rewrite. But we need to verify it works correctly with the test data directory and update the header key references.

**Files:**
- Modify: `tests/test_ecostress_adapter.py` (add discover tests)
- Modify: `src/speclib/ingest/ecostress.py` (discover method, if needed)

- [ ] **Step 1: Write failing test for discover()**

Add to `tests/test_ecostress_adapter.py`:

```python
class TestDiscover:
    """Tests for the discover() method."""

    def test_discover_finds_all_spectra(self):
        """discover() finds all .spectrum.txt files in the data dir."""
        adapter = _make_adapter()
        records = adapter.discover()
        # We have 4 spectrum files in test data
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
```

- [ ] **Step 2: Run discover tests**

Run: `pytest tests/test_ecostress_adapter.py::TestDiscover -v`
Expected: Tests should PASS if the header parser rewrite works correctly in `discover()`. If they fail, proceed to Step 3.

- [ ] **Step 3: Fix discover() if needed**

The `discover()` method reads `header.get("Type", "").lower()` which should now return the correct value (e.g., `"mineral"` instead of `"Type: Mineral"`). Verify and fix any remaining key references. The method at line 96-97 should work as-is:

```python
type_str = header.get("Type", "").lower()
category = _TYPE_MAP.get(type_str, "MINERAL")
```

If NPV records fail, ensure `"non photosynthetic vegetation"` maps correctly via `_TYPE_MAP`.

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
ruff check tests/test_ecostress_adapter.py --fix
ruff format tests/test_ecostress_adapter.py
git add tests/test_ecostress_adapter.py src/speclib/ingest/ecostress.py
git commit -m "Add discover() tests for ECOSTRESS adapter"
```

---

### Task 8: Full pipeline integration test

End-to-end test: discover all test spectra, fetch, normalize, write to HDF5, read back and verify.

**Files:**
- Modify: `tests/test_ecostress_adapter.py` (add integration test)

- [ ] **Step 1: Write integration test**

Add to `tests/test_ecostress_adapter.py`:

```python
from speclib.storage.hdf5 import HDF5Archive


class TestFullPipeline:
    """End-to-end integration test: discover -> fetch -> normalize -> HDF5."""

    def test_ingest_all_to_hdf5(self):
        """All test spectra can be ingested and round-tripped through HDF5."""
        adapter = _make_adapter()
        spectra = adapter.ingest_all()
        assert len(spectra) > 0

        with tempfile.TemporaryDirectory() as tmpdir:
            archive = HDF5Archive(Path(tmpdir) / "test_ecostress.h5")
            for spectrum in spectra:
                archive.write(spectrum)

            # Verify all were written
            ids = archive.list_ids()
            assert len(ids) == len(spectra)

            # Verify round-trip for each
            for spectrum in spectra:
                loaded = archive.read(spectrum.spectrum_id)
                assert loaded.name == spectrum.name
                np.testing.assert_array_almost_equal(
                    loaded.wavelengths, spectrum.wavelengths
                )
                np.testing.assert_array_almost_equal(
                    loaded.reflectance, spectrum.reflectance
                )
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
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_ecostress_adapter.py::TestFullPipeline -v`
Expected: All 3 tests PASS.

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
ruff check tests/test_ecostress_adapter.py --fix
ruff format tests/test_ecostress_adapter.py
git add tests/test_ecostress_adapter.py
git commit -m "Add full pipeline integration test for ECOSTRESS adapter"
```

---

### Task 9: Extract full ECOSTRESS library and update config

Extract the full zip, update the YAML config, and verify the adapter can discover all 3,311 spectra.

**Files:**
- Modify: `data/upstream/ecostress.yaml`

- [ ] **Step 1: Extract the zip to the upstream downloads directory**

```bash
mkdir -p data/upstream/downloads/ecostress
```

```python
import zipfile
from pathlib import Path

z = zipfile.ZipFile(r"C:\Users\chris.lyons\Downloads\ecospeclib-1775149306367.zip")
out = Path("data/upstream/downloads/ecostress")
z.extractall(out)
print(f"Extracted {len(z.namelist())} files to {out}")
```

- [ ] **Step 2: Verify extraction**

```bash
ls data/upstream/downloads/ecostress/*.spectrum.txt | wc -l
```

Expected: `3311` (approximately — the exact count of `.spectrum.txt` files).

- [ ] **Step 3: Update ecostress.yaml**

Update `data/upstream/ecostress.yaml` to set `data_dir`:

```yaml
# ECOSTRESS Spectral Library — Ingestion Config
source: ECOSTRESS
version: "1.0"
citation: >
  Meerdink, S.K., Hook, S.J., Roberts, D.A., & Abbott, E.A. (2019).
  The ECOSTRESS spectral library version 1.0.
  Remote Sensing of Environment, 230, 111196.
license: "CC0 / Public Domain"
data_url: "https://speclib.jpl.nasa.gov/"
data_dir: "data/upstream/downloads/ecostress"
```

- [ ] **Step 4: Verify discover() finds all spectra**

```python
from pathlib import Path
from speclib.ingest.ecostress import EcostressAdapter

adapter = EcostressAdapter(Path("data/upstream/ecostress.yaml"))
records = adapter.discover()
print(f"Discovered {len(records)} spectra")

# Check category distribution
from collections import Counter
cats = Counter(r.category for r in records)
for cat, count in cats.most_common():
    print(f"  {cat}: {count}")
```

Expected: ~3,311 spectra discovered across MINERAL, VEGETATION, ROCK, SOIL, NONPHOTOSYNTHETIC_VEGETATION categories.

- [ ] **Step 5: Verify .gitignore excludes the extracted data**

Check that `data/upstream/downloads/` is in `.gitignore`. If not, add it:

```bash
grep -q "data/upstream/downloads" .gitignore || echo "data/upstream/downloads/" >> .gitignore
```

- [ ] **Step 6: Commit config update only (not the extracted data)**

```bash
git add data/upstream/ecostress.yaml .gitignore
git commit -m "Update ECOSTRESS config with data_dir for extracted library"
```

---

### Task 10: Run full ingestion into HDF5 archive

Ingest all 3,311 ECOSTRESS spectra into the HDF5 archive. This is the production ingestion step.

**Files:**
- Creates: HDF5 archive file (not committed to git)

- [ ] **Step 1: Run ingestion**

```python
import logging
from pathlib import Path

from speclib.ingest.ecostress import EcostressAdapter
from speclib.storage.hdf5 import HDF5Archive

logging.basicConfig(level=logging.INFO)

adapter = EcostressAdapter(Path("data/upstream/ecostress.yaml"))
archive = HDF5Archive(Path("data/speclib_archive.h5"))

spectra = adapter.ingest_all()
print(f"Normalized {len(spectra)} spectra")

for i, spectrum in enumerate(spectra):
    archive.write(spectrum)
    if (i + 1) % 500 == 0:
        print(f"  Written {i + 1}/{len(spectra)}")

print(f"Done. Archive: {archive.path}")
```

- [ ] **Step 2: Verify archive contents**

```python
from pathlib import Path
from speclib.storage.hdf5 import HDF5Archive
from speclib.core.spectrum import MaterialCategory

archive = HDF5Archive(Path("data/speclib_archive.h5"))
all_ids = archive.list_ids()
print(f"Total spectra in archive: {len(all_ids)}")

for cat in MaterialCategory:
    ids = archive.list_ids(cat)
    if ids:
        print(f"  {cat.value}: {len(ids)}")
```

Expected: ~3,311 spectra across categories.

- [ ] **Step 3: Spot-check a few spectra**

```python
import numpy as np
from pathlib import Path
from speclib.storage.hdf5 import HDF5Archive

archive = HDF5Archive(Path("data/speclib_archive.h5"))
ids = archive.list_ids()

# Check first 3
for sid in ids[:3]:
    spec = archive.read(sid)
    assert np.all(np.diff(spec.wavelengths) >= 0), f"Wavelengths not ascending: {sid}"
    finite = spec.reflectance[np.isfinite(spec.reflectance)]
    assert np.all(finite <= 1.5), f"Reflectance not fractional: {sid}"
    print(f"{sid}: {spec.name}, {spec.n_bands} bands, "
          f"range {spec.wavelength_range[0]:.2f}-{spec.wavelength_range[1]:.2f} um")
```

- [ ] **Step 4: Final test suite run**

Run: `pytest tests/ -v`
Expected: All tests PASS.

This task does not produce a commit — the HDF5 archive is not committed to git per the data-handling guardrails.

---

## Follow-Up (not part of this plan)

After ingestion completes, run the existing build pipeline to regenerate downstream layers:

1. **Parquet query layer** — Run `storage.parquet.export()` to regenerate `query/` from the HDF5 archive
2. **Static JSON catalog** — Run `build/generate_static.py` to regenerate `web/static/data/`

These use existing code and don't require adapter changes.

## Design Decision: Header Key Preservation

The spec suggested a `_KEY_NORMALIZE` mapping to convert header keys to canonical snake_case forms. This plan instead preserves original header keys as-is (e.g., `"Sample No."`, `"X Units"`) because:
- The `_read_header` function is internal to the adapter
- Keys are only used within `fetch()` and `normalize()` where the original names are clear
- Adding a normalization layer adds complexity without benefit since no external code reads these keys
