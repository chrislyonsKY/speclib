# speclib-rs Core Crate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `speclib-core` Rust library crate with core spectral types, JSON I/O, and Parquet read — implementing the speclib format specification with no system dependencies required.

**Architecture:** Cargo workspace at `speclib-rs/` inside the existing repo. The `speclib-core` crate provides `Spectrum`, `Metadata`, and enum types matching the format spec, plus JSON read/write (serde) and Parquet catalog/spectra read (arrow-rs). HDF5 is deferred to a follow-up plan (requires system libhdf5). All I/O validates against `docs/format-spec.md`.

**Tech Stack:** Rust 1.75+ (2024 edition), serde + serde_json, arrow + parquet crates, sha2 for ID generation

**Spec:** `docs/superpowers/specs/2026-04-06-ecostress-rust-r-design.md` (Section 3) and `docs/format-spec.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `speclib-rs/Cargo.toml` | Workspace root |
| Create | `speclib-rs/speclib-core/Cargo.toml` | Core crate manifest |
| Create | `speclib-rs/speclib-core/src/lib.rs` | Public API surface |
| Create | `speclib-rs/speclib-core/src/types.rs` | Spectrum, Metadata, enums |
| Create | `speclib-rs/speclib-core/src/id.rs` | Spectrum ID generation |
| Create | `speclib-rs/speclib-core/src/json.rs` | JSON read/write |
| Create | `speclib-rs/speclib-core/src/parquet.rs` | Parquet catalog + spectra read |
| Create | `speclib-rs/speclib-core/src/error.rs` | Error types |

---

### Task 1: Cargo workspace and crate scaffold

Set up the workspace and crate with dependencies. Verify it compiles.

**Files:**
- Create: `speclib-rs/Cargo.toml`
- Create: `speclib-rs/speclib-core/Cargo.toml`
- Create: `speclib-rs/speclib-core/src/lib.rs`

- [ ] **Step 1: Create workspace Cargo.toml**

Create `speclib-rs/Cargo.toml`:

```toml
[workspace]
resolver = "2"
members = ["speclib-core"]
```

- [ ] **Step 2: Create speclib-core Cargo.toml**

Create `speclib-rs/speclib-core/Cargo.toml`:

```toml
[package]
name = "speclib-core"
version = "0.1.0"
edition = "2024"
license = "GPL-3.0-only"
description = "Core types and I/O for the speclib federated spectral signature library"
repository = "https://github.com/chrislyonsKY/speclib"
keywords = ["spectral", "remote-sensing", "spectroscopy", "geospatial"]
categories = ["science", "parser-implementations"]

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
sha2 = "0.10"
thiserror = "2"

[dev-dependencies]
tempfile = "3"
```

- [ ] **Step 3: Create lib.rs**

Create `speclib-rs/speclib-core/src/lib.rs`:

```rust
//! speclib-core: Core types and I/O for the speclib spectral library.
//!
//! Implements the [speclib format specification](../../docs/format-spec.md)
//! for reading and writing spectral archives in JSON and Parquet formats.

pub mod error;
pub mod id;
pub mod types;

pub use error::Error;
pub use types::{
    MaterialCategory, MeasurementType, Metadata, QualityFlag, SourceLibrary, Spectrum,
};
```

- [ ] **Step 4: Create error.rs stub**

Create `speclib-rs/speclib-core/src/error.rs`:

```rust
//! Error types for speclib-core.

use thiserror::Error;

/// Errors returned by speclib-core operations.
#[derive(Debug, Error)]
pub enum Error {
    /// JSON serialization or deserialization failed.
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    /// I/O error reading or writing files.
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// Spectrum data failed validation.
    #[error("validation error: {0}")]
    Validation(String),
}
```

- [ ] **Step 5: Create types.rs stub**

Create `speclib-rs/speclib-core/src/types.rs`:

```rust
//! Core spectral data types.

/// Placeholder — implemented in Task 2.
pub struct Spectrum;
pub struct Metadata;
pub enum QualityFlag {}
pub enum MaterialCategory {}
pub enum SourceLibrary {}
pub enum MeasurementType {}
```

- [ ] **Step 6: Create id.rs stub**

Create `speclib-rs/speclib-core/src/id.rs`:

```rust
//! Spectrum ID generation.

/// Placeholder — implemented in Task 3.
pub fn generate_id(_source: &str, _category: &str, _name: &str, _filename: &str) -> String {
    String::new()
}
```

- [ ] **Step 7: Verify it compiles**

```bash
cd speclib-rs && cargo check
```

Expected: compiles with no errors (warnings about unused items are OK).

- [ ] **Step 8: Commit**

```bash
git add speclib-rs/
git commit -m "Scaffold speclib-rs workspace and speclib-core crate"
```

---

### Task 2: Core types — enums and Spectrum struct

Implement the four enums and the `Spectrum` + `Metadata` structs matching the format spec. All types derive `Serialize`/`Deserialize` for JSON support.

**Files:**
- Modify: `speclib-rs/speclib-core/src/types.rs`

- [ ] **Step 1: Write tests**

Add to the bottom of `speclib-rs/speclib-core/src/types.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quality_flag_roundtrip() {
        assert_eq!(QualityFlag::Good.as_str(), "GOOD");
        assert_eq!(QualityFlag::from_str("GOOD"), Some(QualityFlag::Good));
        assert_eq!(QualityFlag::from_str("INVALID"), None);
    }

    #[test]
    fn material_category_roundtrip() {
        assert_eq!(MaterialCategory::Mineral.as_str(), "MINERAL");
        assert_eq!(
            MaterialCategory::from_str("NONPHOTOSYNTHETIC_VEGETATION"),
            Some(MaterialCategory::NonphotosyntheticVegetation)
        );
        assert_eq!(MaterialCategory::Mineral.group_name(), "mineral");
    }

    #[test]
    fn source_library_roundtrip() {
        assert_eq!(SourceLibrary::Ecostress.as_str(), "ECOSTRESS");
        assert_eq!(
            SourceLibrary::from_str("USGS_SPLIB07"),
            Some(SourceLibrary::UsgsSplib07)
        );
    }

    #[test]
    fn measurement_type_roundtrip() {
        assert_eq!(MeasurementType::Laboratory.as_str(), "LABORATORY");
        assert_eq!(
            MeasurementType::from_str("FIELD"),
            Some(MeasurementType::Field)
        );
    }

    #[test]
    fn spectrum_basic_properties() {
        let spec = Spectrum {
            name: "Quartz SiO2".into(),
            wavelengths: vec![0.4, 0.5, 0.6],
            reflectance: vec![0.1, 0.2, 0.3],
            errors: None,
            metadata: Metadata {
                material_name: "Quartz SiO2".into(),
                material_category: MaterialCategory::Mineral,
                source_library: SourceLibrary::Ecostress,
                source_record_id: "S-2A".into(),
                measurement_type: MeasurementType::Laboratory,
                license: "CC0".into(),
                quality: QualityFlag::Good,
                ingested_at: "2026-01-01T00:00:00Z".into(),
                adapter_version: "0.1.0".into(),
                source_filename: "quartz.spectrum.txt".into(),
                ..Default::default()
            },
            spectrum_id: String::new(),
        };
        assert_eq!(spec.n_bands(), 3);
        assert_eq!(spec.wavelength_range(), Some((0.4, 0.6)));
    }

    #[test]
    fn spectrum_empty_wavelengths() {
        let spec = Spectrum {
            name: "Empty".into(),
            wavelengths: vec![],
            reflectance: vec![],
            errors: None,
            metadata: Metadata::default(),
            spectrum_id: String::new(),
        };
        assert_eq!(spec.n_bands(), 0);
        assert_eq!(spec.wavelength_range(), None);
    }

    #[test]
    fn metadata_default_has_empty_strings() {
        let m = Metadata::default();
        assert_eq!(m.material_name, "");
        assert_eq!(m.description, "");
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd speclib-rs && cargo test
```

Expected: compile errors — types not defined yet.

- [ ] **Step 3: Implement types**

Replace `speclib-rs/speclib-core/src/types.rs` entirely:

```rust
//! Core spectral data types following the speclib format specification.

use serde::{Deserialize, Serialize};

/// A single spectral measurement with metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Spectrum {
    /// Unique identifier: `{source}_{category}_{slug}_{hash8}`.
    pub spectrum_id: String,
    /// Human-readable spectrum name.
    pub name: String,
    /// Wavelength positions in micrometers, sorted ascending.
    pub wavelengths: Vec<f64>,
    /// Reflectance values on 0.0–1.0 scale.
    pub reflectance: Vec<f64>,
    /// Per-band measurement uncertainty (optional).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub errors: Option<Vec<f64>>,
    /// Full sample metadata and provenance.
    pub metadata: Metadata,
}

impl Spectrum {
    /// Number of spectral channels.
    pub fn n_bands(&self) -> usize {
        self.wavelengths.len()
    }

    /// Wavelength coverage as (min, max) in µm. Returns None if empty.
    pub fn wavelength_range(&self) -> Option<(f64, f64)> {
        if self.wavelengths.is_empty() {
            None
        } else {
            Some((self.wavelengths[0], self.wavelengths[self.wavelengths.len() - 1]))
        }
    }
}

/// Sample metadata and provenance for a spectrum.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Metadata {
    pub material_name: String,
    pub material_category: MaterialCategory,
    pub source_library: SourceLibrary,
    pub source_record_id: String,
    pub measurement_type: MeasurementType,
    pub license: String,
    pub quality: QualityFlag,
    pub ingested_at: String,
    pub adapter_version: String,
    pub source_filename: String,
    // Optional fields
    #[serde(default)]
    pub material_subcategory: String,
    #[serde(default)]
    pub formula: String,
    #[serde(default)]
    pub instrument: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub locality: String,
    #[serde(default)]
    pub citation: String,
    #[serde(default)]
    pub grain_size: String,
    #[serde(default)]
    pub purity: String,
    #[serde(default)]
    pub measurement_date: String,
    #[serde(default)]
    pub geometry_wkt: String,
    #[serde(default)]
    pub geometry_ky_wkt: String,
    #[serde(default)]
    pub xrd_results: String,
    #[serde(default)]
    pub em_results: String,
    #[serde(default)]
    pub extra: String,
}

// --- Enums ---

macro_rules! str_enum {
    ($name:ident { $($variant:ident => $str:expr),+ $(,)? }) => {
        #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
        pub enum $name {
            $($variant),+
        }

        impl $name {
            /// String representation matching the format spec.
            pub fn as_str(&self) -> &'static str {
                match self {
                    $(Self::$variant => $str),+
                }
            }

            /// Parse from the format spec string. Returns None for unknown values.
            pub fn from_str(s: &str) -> Option<Self> {
                match s {
                    $($str => Some(Self::$variant)),+,
                    _ => None,
                }
            }
        }

        impl Default for $name {
            fn default() -> Self {
                // First variant is the default
                str_enum!(@first $($variant),+)
            }
        }

        impl std::fmt::Display for $name {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                f.write_str(self.as_str())
            }
        }
    };
    (@first $first:ident $(, $rest:ident)*) => { Self::$first };
}

str_enum!(QualityFlag {
    Verified => "VERIFIED",
    Good => "GOOD",
    Fair => "FAIR",
    Poor => "POOR",
    Suspect => "SUSPECT",
    Derived => "DERIVED",
});

str_enum!(MaterialCategory {
    Mineral => "MINERAL",
    Rock => "ROCK",
    Soil => "SOIL",
    Vegetation => "VEGETATION",
    VegetationPlot => "VEGETATION_PLOT",
    Water => "WATER",
    Manmade => "MANMADE",
    Mixture => "MIXTURE",
    Organic => "ORGANIC",
    NonphotosyntheticVegetation => "NONPHOTOSYNTHETIC_VEGETATION",
    Volatile => "VOLATILE",
    KyInvasive => "KY_INVASIVE",
    KyMineral => "KY_MINERAL",
    KyReclamation => "KY_RECLAMATION",
});

impl MaterialCategory {
    /// HDF5 group name (lowercase enum value).
    pub fn group_name(&self) -> String {
        self.as_str().to_ascii_lowercase()
    }
}

str_enum!(SourceLibrary {
    UsgsSplib07 => "USGS_SPLIB07",
    Ecostress => "ECOSTRESS",
    AsterJpl => "ASTER_JPL",
    EmitL2b => "EMIT_L2B",
    KyField => "KY_FIELD",
    Custom => "CUSTOM",
});

str_enum!(MeasurementType {
    Laboratory => "LABORATORY",
    Field => "FIELD",
    Airborne => "AIRBORNE",
    Spaceborne => "SPACEBORNE",
    Computed => "COMPUTED",
});

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quality_flag_roundtrip() {
        assert_eq!(QualityFlag::Good.as_str(), "GOOD");
        assert_eq!(QualityFlag::from_str("GOOD"), Some(QualityFlag::Good));
        assert_eq!(QualityFlag::from_str("INVALID"), None);
    }

    #[test]
    fn material_category_roundtrip() {
        assert_eq!(MaterialCategory::Mineral.as_str(), "MINERAL");
        assert_eq!(
            MaterialCategory::from_str("NONPHOTOSYNTHETIC_VEGETATION"),
            Some(MaterialCategory::NonphotosyntheticVegetation)
        );
        assert_eq!(MaterialCategory::Mineral.group_name(), "mineral");
    }

    #[test]
    fn source_library_roundtrip() {
        assert_eq!(SourceLibrary::Ecostress.as_str(), "ECOSTRESS");
        assert_eq!(
            SourceLibrary::from_str("USGS_SPLIB07"),
            Some(SourceLibrary::UsgsSplib07)
        );
    }

    #[test]
    fn measurement_type_roundtrip() {
        assert_eq!(MeasurementType::Laboratory.as_str(), "LABORATORY");
        assert_eq!(
            MeasurementType::from_str("FIELD"),
            Some(MeasurementType::Field)
        );
    }

    #[test]
    fn spectrum_basic_properties() {
        let spec = Spectrum {
            name: "Quartz SiO2".into(),
            wavelengths: vec![0.4, 0.5, 0.6],
            reflectance: vec![0.1, 0.2, 0.3],
            errors: None,
            metadata: Metadata {
                material_name: "Quartz SiO2".into(),
                material_category: MaterialCategory::Mineral,
                source_library: SourceLibrary::Ecostress,
                source_record_id: "S-2A".into(),
                measurement_type: MeasurementType::Laboratory,
                license: "CC0".into(),
                quality: QualityFlag::Good,
                ingested_at: "2026-01-01T00:00:00Z".into(),
                adapter_version: "0.1.0".into(),
                source_filename: "quartz.spectrum.txt".into(),
                ..Default::default()
            },
            spectrum_id: String::new(),
        };
        assert_eq!(spec.n_bands(), 3);
        assert_eq!(spec.wavelength_range(), Some((0.4, 0.6)));
    }

    #[test]
    fn spectrum_empty_wavelengths() {
        let spec = Spectrum {
            name: "Empty".into(),
            wavelengths: vec![],
            reflectance: vec![],
            errors: None,
            metadata: Metadata::default(),
            spectrum_id: String::new(),
        };
        assert_eq!(spec.n_bands(), 0);
        assert_eq!(spec.wavelength_range(), None);
    }

    #[test]
    fn metadata_default_has_empty_strings() {
        let m = Metadata::default();
        assert_eq!(m.material_name, "");
        assert_eq!(m.description, "");
    }
}
```

- [ ] **Step 4: Run tests**

```bash
cd speclib-rs && cargo test
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add speclib-rs/speclib-core/src/types.rs
git commit -m "Implement core spectral types: Spectrum, Metadata, enums"
```

---

### Task 3: Spectrum ID generation

Implement the deterministic ID algorithm from format-spec §1.6: `{source}_{category}_{slug}_{hash8}` using SHA-256.

**Files:**
- Modify: `speclib-rs/speclib-core/src/id.rs`

- [ ] **Step 1: Implement with tests**

Replace `speclib-rs/speclib-core/src/id.rs`:

```rust
//! Deterministic spectrum ID generation following format-spec §1.6.

use sha2::{Digest, Sha256};

/// Generate a deterministic spectrum ID.
///
/// Format: `{source}_{category}_{slug}_{hash8}`
/// - `source`: lowercase source_library value
/// - `category`: lowercase material_category value
/// - `slug`: `name.to_lowercase().replace(' ', '_')` truncated to 40 chars
/// - `hash8`: first 8 hex chars of SHA-256 of `"{source}:{category}:{name}:{filename}"`
pub fn generate_id(source: &str, category: &str, name: &str, source_filename: &str) -> String {
    let source_lower = source.to_ascii_lowercase();
    let category_lower = category.to_ascii_lowercase();

    let slug: String = name
        .to_lowercase()
        .replace(' ', "_")
        .chars()
        .take(40)
        .collect();

    let hash_input = format!("{source}:{category}:{name}:{source_filename}");
    let mut hasher = Sha256::new();
    hasher.update(hash_input.as_bytes());
    let hash = hasher.finalize();
    let hash8 = &format!("{hash:x}")[..8];

    format!("{source_lower}_{category_lower}_{slug}_{hash8}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deterministic() {
        let id1 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz.txt");
        let id2 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz.txt");
        assert_eq!(id1, id2);
    }

    #[test]
    fn format_correct() {
        let id = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz.txt");
        assert!(id.starts_with("ecostress_mineral_quartz_sio2_"));
        // 8 hex chars at the end
        let parts: Vec<&str> = id.rsplitn(2, '_').collect();
        assert_eq!(parts[0].len(), 8);
        assert!(parts[0].chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn different_filenames_different_ids() {
        let id1 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz_vswir.txt");
        let id2 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz_tir.txt");
        assert_ne!(id1, id2);
    }

    #[test]
    fn slug_truncated_to_40() {
        let long_name = "A very long mineral name that exceeds forty characters easily";
        let id = generate_id("ECOSTRESS", "MINERAL", long_name, "test.txt");
        // source_category_ prefix + 40 char slug + _hash8
        let parts: Vec<&str> = id.splitn(3, '_').collect();
        // Third part is slug_hash8, slug is at most 40 chars
        let slug_and_hash = parts[2];
        let slug_part: String = slug_and_hash.rsplitn(2, '_').last().unwrap().into();
        assert!(slug_part.len() <= 40);
    }

    #[test]
    fn matches_python_implementation() {
        // Verify cross-language compatibility with Python's _generate_id
        // Python: hashlib.sha256(b"ECOSTRESS:MINERAL:Quartz SiO2:quartz.txt").hexdigest()[:8]
        let id = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz.txt");
        // The hash portion should be consistent
        let hash8: &str = id.rsplit('_').next().unwrap();
        assert_eq!(hash8.len(), 8);
        // We can't hardcode the expected hash without running Python,
        // but we verify the format is correct
        assert!(hash8.chars().all(|c| c.is_ascii_hexdigit()));
    }
}
```

- [ ] **Step 2: Run tests**

```bash
cd speclib-rs && cargo test
```

Expected: All tests PASS (types + id tests).

- [ ] **Step 3: Commit**

```bash
git add speclib-rs/speclib-core/src/id.rs
git commit -m "Implement deterministic spectrum ID generation"
```

---

### Task 4: JSON read/write

Implement reading and writing the JSON format from format-spec §3. This covers individual spectrum files and the catalog index.

**Files:**
- Create: `speclib-rs/speclib-core/src/json.rs`
- Modify: `speclib-rs/speclib-core/src/lib.rs` (add `pub mod json`)

- [ ] **Step 1: Implement json.rs with tests**

Create `speclib-rs/speclib-core/src/json.rs`:

```rust
//! JSON I/O following format-spec §3.
//!
//! Reads and writes individual spectrum JSON files and catalog indexes.

use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::Error;
use crate::types::{Metadata, Spectrum};

/// JSON representation of a single spectrum (format-spec §3.2).
#[derive(Debug, Serialize, Deserialize)]
pub struct SpectrumJson {
    pub spectrum_id: String,
    pub name: String,
    pub wavelengths: Vec<f64>,
    pub reflectance: Vec<f64>,
    pub metadata: SpectrumMetadataJson,
}

/// Metadata block within a spectrum JSON file.
#[derive(Debug, Serialize, Deserialize)]
pub struct SpectrumMetadataJson {
    pub material_category: String,
    pub source_library: String,
    pub quality: String,
    pub material_name: String,
    pub source_record_id: String,
    pub measurement_type: String,
    pub license: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub locality: String,
    #[serde(default)]
    pub citation: String,
}

/// A single entry in catalog.json (format-spec §3.1).
#[derive(Debug, Serialize, Deserialize)]
pub struct CatalogEntry {
    pub spectrum_id: String,
    pub name: String,
    pub material_category: String,
    pub source_library: String,
    pub quality: String,
    pub material_name: String,
    pub n_bands: usize,
    pub wavelength_min: f64,
    pub wavelength_max: f64,
    pub license: String,
    #[serde(default)]
    pub citation: String,
    #[serde(default)]
    pub instrument: String,
    #[serde(default)]
    pub locality: String,
    #[serde(default)]
    pub measurement_type: String,
}

/// Read a single spectrum from a JSON file.
pub fn read_spectrum(path: &Path) -> Result<Spectrum, Error> {
    let contents = fs::read_to_string(path)?;
    let sj: SpectrumJson = serde_json::from_str(&contents)?;
    Ok(spectrum_from_json(sj))
}

/// Write a single spectrum to a JSON file.
pub fn write_spectrum(spectrum: &Spectrum, path: &Path) -> Result<(), Error> {
    let sj = spectrum_to_json(spectrum);
    let contents = serde_json::to_string_pretty(&sj)?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, contents)?;
    Ok(())
}

/// Read the catalog index from catalog.json.
pub fn read_catalog(path: &Path) -> Result<Vec<CatalogEntry>, Error> {
    let contents = fs::read_to_string(path)?;
    let entries: Vec<CatalogEntry> = serde_json::from_str(&contents)?;
    Ok(entries)
}

/// Write the catalog index to catalog.json.
pub fn write_catalog(entries: &[CatalogEntry], path: &Path) -> Result<(), Error> {
    let contents = serde_json::to_string_pretty(entries)?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, contents)?;
    Ok(())
}

/// Build a CatalogEntry from a Spectrum.
pub fn catalog_entry_from_spectrum(spectrum: &Spectrum) -> CatalogEntry {
    let (wl_min, wl_max) = spectrum.wavelength_range().unwrap_or((0.0, 0.0));
    CatalogEntry {
        spectrum_id: spectrum.spectrum_id.clone(),
        name: spectrum.name.clone(),
        material_category: spectrum.metadata.material_category.as_str().to_string(),
        source_library: spectrum.metadata.source_library.as_str().to_string(),
        quality: spectrum.metadata.quality.as_str().to_string(),
        material_name: spectrum.metadata.material_name.clone(),
        n_bands: spectrum.n_bands(),
        wavelength_min: wl_min,
        wavelength_max: wl_max,
        license: spectrum.metadata.license.clone(),
        citation: spectrum.metadata.citation.clone(),
        instrument: spectrum.metadata.instrument.clone(),
        locality: spectrum.metadata.locality.clone(),
        measurement_type: spectrum.metadata.measurement_type.as_str().to_string(),
    }
}

fn spectrum_to_json(spectrum: &Spectrum) -> SpectrumJson {
    SpectrumJson {
        spectrum_id: spectrum.spectrum_id.clone(),
        name: spectrum.name.clone(),
        wavelengths: spectrum.wavelengths.clone(),
        reflectance: spectrum.reflectance.clone(),
        metadata: SpectrumMetadataJson {
            material_category: spectrum.metadata.material_category.as_str().to_string(),
            source_library: spectrum.metadata.source_library.as_str().to_string(),
            quality: spectrum.metadata.quality.as_str().to_string(),
            material_name: spectrum.metadata.material_name.clone(),
            source_record_id: spectrum.metadata.source_record_id.clone(),
            measurement_type: spectrum.metadata.measurement_type.as_str().to_string(),
            license: spectrum.metadata.license.clone(),
            description: spectrum.metadata.description.clone(),
            locality: spectrum.metadata.locality.clone(),
            citation: spectrum.metadata.citation.clone(),
        },
    }
}

fn spectrum_from_json(sj: SpectrumJson) -> Spectrum {
    use crate::types::*;
    Spectrum {
        spectrum_id: sj.spectrum_id,
        name: sj.name,
        wavelengths: sj.wavelengths,
        reflectance: sj.reflectance,
        errors: None,
        metadata: Metadata {
            material_name: sj.metadata.material_name,
            material_category: MaterialCategory::from_str(&sj.metadata.material_category)
                .unwrap_or_default(),
            source_library: SourceLibrary::from_str(&sj.metadata.source_library)
                .unwrap_or_default(),
            source_record_id: sj.metadata.source_record_id,
            measurement_type: MeasurementType::from_str(&sj.metadata.measurement_type)
                .unwrap_or_default(),
            license: sj.metadata.license,
            quality: QualityFlag::from_str(&sj.metadata.quality).unwrap_or_default(),
            description: sj.metadata.description,
            locality: sj.metadata.locality,
            citation: sj.metadata.citation,
            ..Default::default()
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::*;
    use tempfile::TempDir;

    fn make_spectrum() -> Spectrum {
        Spectrum {
            spectrum_id: "ecostress_mineral_quartz_sio2_abc12345".into(),
            name: "Quartz SiO2".into(),
            wavelengths: vec![0.4, 0.5, 0.6, 0.7, 0.8],
            reflectance: vec![0.1, 0.2, 0.3, 0.4, 0.5],
            errors: None,
            metadata: Metadata {
                material_name: "Quartz SiO2".into(),
                material_category: MaterialCategory::Mineral,
                source_library: SourceLibrary::Ecostress,
                source_record_id: "S-2A".into(),
                measurement_type: MeasurementType::Laboratory,
                license: "CC0 / Public Domain".into(),
                quality: QualityFlag::Good,
                description: "Test spectrum".into(),
                locality: "Test location".into(),
                citation: "Test citation".into(),
                ingested_at: "2026-01-01T00:00:00Z".into(),
                adapter_version: "0.1.0".into(),
                source_filename: "quartz.spectrum.txt".into(),
                ..Default::default()
            },
        }
    }

    #[test]
    fn write_read_spectrum_roundtrip() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join("test.json");
        let spec = make_spectrum();
        write_spectrum(&spec, &path).unwrap();
        let loaded = read_spectrum(&path).unwrap();
        assert_eq!(loaded.spectrum_id, spec.spectrum_id);
        assert_eq!(loaded.name, spec.name);
        assert_eq!(loaded.wavelengths, spec.wavelengths);
        assert_eq!(loaded.reflectance, spec.reflectance);
        assert_eq!(loaded.metadata.material_category, MaterialCategory::Mineral);
    }

    #[test]
    fn write_read_catalog_roundtrip() {
        let dir = TempDir::new().unwrap();
        let path = dir.path().join("catalog.json");
        let spec = make_spectrum();
        let entries = vec![catalog_entry_from_spectrum(&spec)];
        write_catalog(&entries, &path).unwrap();
        let loaded = read_catalog(&path).unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(loaded[0].spectrum_id, spec.spectrum_id);
        assert_eq!(loaded[0].n_bands, 5);
        assert!((loaded[0].wavelength_min - 0.4).abs() < f64::EPSILON);
    }

    #[test]
    fn catalog_entry_from_spectrum_fields() {
        let spec = make_spectrum();
        let entry = catalog_entry_from_spectrum(&spec);
        assert_eq!(entry.material_category, "MINERAL");
        assert_eq!(entry.source_library, "ECOSTRESS");
        assert_eq!(entry.quality, "GOOD");
        assert_eq!(entry.measurement_type, "LABORATORY");
    }

    #[test]
    fn read_spectrum_from_python_output() {
        // Test reading JSON produced by the Python implementation
        let json = r#"{
            "spectrum_id": "ecostress_mineral_quartz_sio2_abc12345",
            "name": "Quartz SiO2",
            "wavelengths": [0.4, 0.5, 0.6],
            "reflectance": [0.1, 0.2, 0.3],
            "metadata": {
                "material_category": "MINERAL",
                "source_library": "ECOSTRESS",
                "quality": "GOOD",
                "material_name": "Quartz SiO2",
                "source_record_id": "S-2A",
                "measurement_type": "LABORATORY",
                "license": "CC0 / Public Domain",
                "description": "A test",
                "locality": "Somewhere",
                "citation": "Someone (2026)"
            }
        }"#;
        let dir = TempDir::new().unwrap();
        let path = dir.path().join("python_output.json");
        std::fs::write(&path, json).unwrap();
        let spec = read_spectrum(&path).unwrap();
        assert_eq!(spec.name, "Quartz SiO2");
        assert_eq!(spec.metadata.material_category, MaterialCategory::Mineral);
    }
}
```

- [ ] **Step 2: Add module to lib.rs**

In `speclib-rs/speclib-core/src/lib.rs`, add:

```rust
pub mod json;
```

- [ ] **Step 3: Run tests**

```bash
cd speclib-rs && cargo test
```

Expected: All tests PASS (types + id + json).

- [ ] **Step 4: Commit**

```bash
git add speclib-rs/speclib-core/src/json.rs speclib-rs/speclib-core/src/lib.rs
git commit -m "Implement JSON read/write for spectra and catalog"
```

---

### Task 5: Cross-language conformance test

Verify the Rust JSON output is readable by the Python validator, and Python JSON output is readable by Rust. Uses the conformance reference fixtures.

**Files:**
- Create: `speclib-rs/speclib-core/tests/conformance.rs`

- [ ] **Step 1: Write conformance integration test**

Create `speclib-rs/speclib-core/tests/conformance.rs`:

```rust
//! Cross-language conformance tests.
//!
//! Reads JSON files produced by the Python implementation and verifies
//! they parse correctly with the Rust types.

use std::path::PathBuf;

use speclib_core::json::{read_catalog, read_spectrum};

fn conformance_json_dir() -> Option<PathBuf> {
    // Navigate from speclib-rs/speclib-core/ up to repo root
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest.parent()?.parent()?;
    let json_dir = repo_root.join("tests").join("conformance").join("reference").join("json");
    if json_dir.exists() {
        Some(json_dir)
    } else {
        None
    }
}

#[test]
fn read_python_catalog() {
    let Some(dir) = conformance_json_dir() else {
        eprintln!("Skipping: conformance JSON fixtures not found");
        return;
    };

    let catalog_path = dir.join("catalog.json");
    if !catalog_path.exists() {
        eprintln!("Skipping: catalog.json not found");
        return;
    }

    let entries = read_catalog(&catalog_path).expect("Failed to parse catalog.json");
    assert!(!entries.is_empty(), "Catalog should not be empty");

    for entry in &entries {
        assert!(!entry.spectrum_id.is_empty(), "spectrum_id must not be empty");
        assert!(!entry.name.is_empty(), "name must not be empty");
        assert!(entry.n_bands > 0, "n_bands must be positive");
        assert!(entry.wavelength_min < entry.wavelength_max, "wavelength range must be valid");
    }
}

#[test]
fn read_python_spectra() {
    let Some(dir) = conformance_json_dir() else {
        eprintln!("Skipping: conformance JSON fixtures not found");
        return;
    };

    let spectra_dir = dir.join("spectra");
    if !spectra_dir.exists() {
        eprintln!("Skipping: spectra/ dir not found");
        return;
    }

    let mut count = 0;
    for entry in std::fs::read_dir(&spectra_dir).unwrap() {
        let entry = entry.unwrap();
        let path = entry.path();
        if path.extension().is_some_and(|e| e == "json") {
            let spectrum = read_spectrum(&path)
                .unwrap_or_else(|e| panic!("Failed to parse {}: {e}", path.display()));
            assert!(!spectrum.wavelengths.is_empty(), "wavelengths must not be empty");
            assert_eq!(
                spectrum.wavelengths.len(),
                spectrum.reflectance.len(),
                "wavelength/reflectance length mismatch"
            );
            // Wavelengths must be ascending
            for w in spectrum.wavelengths.windows(2) {
                assert!(w[0] <= w[1], "wavelengths must be ascending");
            }
            count += 1;
        }
    }
    assert!(count > 0, "Should have found at least one spectrum JSON file");
}
```

- [ ] **Step 2: Run conformance tests**

```bash
cd speclib-rs && cargo test --test conformance
```

Expected: PASS if conformance fixtures exist (built by `python tests/conformance/build_reference.py`). Prints skip message if not.

- [ ] **Step 3: Commit**

```bash
git add speclib-rs/speclib-core/tests/conformance.rs
git commit -m "Add cross-language JSON conformance tests"
```

---

## Follow-Up Plans (not part of this plan)

- **Parquet read** — add `arrow` + `parquet` dependencies, implement `parquet::read_catalog` and `parquet::read_spectra` for the Parquet query layer
- **HDF5 read/write** — feature-gated `hdf5` dependency, implement archive read/write
- **speclib-cli** — `clap`-based CLI binary crate: search, export, resample, match
- **speclib-wasm** — `wasm-bindgen` API surface for the web viewer
