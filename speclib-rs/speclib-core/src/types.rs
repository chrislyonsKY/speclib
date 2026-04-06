//! Core spectral types: Spectrum, Metadata, and classification enums.

use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// str_enum! macro — reduces boilerplate for string-backed enums
// ---------------------------------------------------------------------------

macro_rules! str_enum {
    ($name:ident { $($variant:ident => $str:expr),+ $(,)? }) => {
        #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
        pub enum $name {
            $($variant),+
        }

        impl $name {
            /// String representation matching the format spec.
            pub fn as_str(&self) -> &'static str {
                match self { $(Self::$variant => $str),+ }
            }
        }

        impl std::str::FromStr for $name {
            type Err = String;
            fn from_str(s: &str) -> Result<Self, Self::Err> {
                match s {
                    $($str => Ok(Self::$variant)),+,
                    _ => Err(format!("unknown {} value: {s}", stringify!($name))),
                }
            }
        }

        impl Default for $name {
            fn default() -> Self { str_enum!(@first $($variant),+) }
        }

        impl std::fmt::Display for $name {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                f.write_str(self.as_str())
            }
        }
    };
    (@first $first:ident $(, $rest:ident)*) => { Self::$first };
}

// ---------------------------------------------------------------------------
// Enums (field-schema §4)
// ---------------------------------------------------------------------------

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
    /// Returns the lowercase group name for HDF5/Parquet grouping.
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

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

/// Comprehensive sample documentation following USGS conventions.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Metadata {
    /// Canonical material name.
    pub material_name: String,
    /// Top-level classification.
    pub material_category: MaterialCategory,
    /// Finer classification within category.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub material_subcategory: Option<String>,
    /// Chemical formula (minerals) or species binomial (vegetation).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub formula: Option<String>,
    /// Which upstream library this came from.
    pub source_library: SourceLibrary,
    /// Original record ID in source library.
    pub source_record_id: String,
    /// Original filename in source distribution.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_filename: Option<String>,
    /// Spectrometer used.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub instrument: Option<String>,
    /// Lab, field, or airborne.
    pub measurement_type: MeasurementType,
    /// When the measurement was taken (ISO 8601 date string).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub measurement_date: Option<String>,
    /// Grain/particle size description.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub grain_size: Option<String>,
    /// Sample purity description.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub purity: Option<String>,
    /// X-ray diffraction results summary.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub xrd_results: Option<String>,
    /// Electron microprobe results summary.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub em_results: Option<String>,
    /// Free-text sample description.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    /// Where sample was collected.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub locality: Option<String>,
    /// Publication reference.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub citation: Option<String>,
    /// Data license (e.g., "US Public Domain", "CC0", "CC-BY-4.0").
    pub license: String,
    /// When this record was added to speclib (ISO 8601).
    pub ingested_at: String,
    /// Version of the ingestion adapter used.
    pub adapter_version: String,
    /// Overall quality assessment.
    pub quality: QualityFlag,
}

// ---------------------------------------------------------------------------
// Spectrum
// ---------------------------------------------------------------------------

/// A single spectral measurement with metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Spectrum {
    /// Unique identifier (format: `{source}_{category}_{name}_{hash8}`).
    pub spectrum_id: String,
    /// Human-readable name.
    pub name: String,
    /// Wavelength positions in micrometers (µm), sorted ascending.
    pub wavelengths: Vec<f64>,
    /// Reflectance values (0.0–1.0 scale).
    pub reflectance: Vec<f64>,
    /// Measurement uncertainty per band (same units as reflectance).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub errors: Option<Vec<f64>>,
    /// Full sample description and provenance.
    pub metadata: Metadata,
}

impl Spectrum {
    /// Returns the number of spectral bands.
    pub fn n_bands(&self) -> usize {
        self.wavelengths.len()
    }

    /// Returns `(min_wavelength, max_wavelength)` in µm, or `None` if empty.
    pub fn wavelength_range(&self) -> Option<(f64, f64)> {
        if self.wavelengths.is_empty() {
            return None;
        }
        let mut min = f64::INFINITY;
        let mut max = f64::NEG_INFINITY;
        for &w in &self.wavelengths {
            if w < min {
                min = w;
            }
            if w > max {
                max = w;
            }
        }
        Some((min, max))
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quality_flag_roundtrip() {
        assert_eq!(QualityFlag::Verified.as_str(), "VERIFIED");
        assert_eq!("VERIFIED".parse::<QualityFlag>().unwrap(), QualityFlag::Verified);
        assert_eq!("GOOD".parse::<QualityFlag>().unwrap(), QualityFlag::Good);
        assert!("INVALID".parse::<QualityFlag>().is_err());
    }

    #[test]
    fn material_category_roundtrip() {
        assert_eq!(MaterialCategory::Mineral.as_str(), "MINERAL");
        assert_eq!("MINERAL".parse::<MaterialCategory>().unwrap(), MaterialCategory::Mineral);
        assert_eq!(
            "NONPHOTOSYNTHETIC_VEGETATION".parse::<MaterialCategory>().unwrap(),
            MaterialCategory::NonphotosyntheticVegetation
        );
    }

    #[test]
    fn material_category_group_name() {
        assert_eq!(MaterialCategory::Mineral.group_name(), "mineral");
        assert_eq!(
            MaterialCategory::VegetationPlot.group_name(),
            "vegetation_plot"
        );
        assert_eq!(
            MaterialCategory::KyInvasive.group_name(),
            "ky_invasive"
        );
    }

    #[test]
    fn source_library_roundtrip() {
        assert_eq!(SourceLibrary::UsgsSplib07.as_str(), "USGS_SPLIB07");
        assert_eq!("USGS_SPLIB07".parse::<SourceLibrary>().unwrap(), SourceLibrary::UsgsSplib07);
        assert_eq!("ECOSTRESS".parse::<SourceLibrary>().unwrap(), SourceLibrary::Ecostress);
        assert!("NONEXISTENT".parse::<SourceLibrary>().is_err());
    }

    #[test]
    fn measurement_type_roundtrip() {
        assert_eq!(MeasurementType::Laboratory.as_str(), "LABORATORY");
        assert_eq!("FIELD".parse::<MeasurementType>().unwrap(), MeasurementType::Field);
        assert_eq!("SPACEBORNE".parse::<MeasurementType>().unwrap(), MeasurementType::Spaceborne);
        assert!("UNKNOWN".parse::<MeasurementType>().is_err());
    }

    #[test]
    fn spectrum_basic_properties() {
        let s = Spectrum {
            spectrum_id: "test_mineral_quartz_12345678".into(),
            name: "Quartz".into(),
            wavelengths: vec![0.4, 0.5, 0.6, 0.7],
            reflectance: vec![0.1, 0.2, 0.3, 0.4],
            errors: None,
            metadata: Metadata::default(),
        };
        assert_eq!(s.n_bands(), 4);
        assert_eq!(s.wavelength_range(), Some((0.4, 0.7)));
    }

    #[test]
    fn spectrum_empty_wavelengths() {
        let s = Spectrum {
            spectrum_id: "test_empty".into(),
            name: "Empty".into(),
            wavelengths: vec![],
            reflectance: vec![],
            errors: None,
            metadata: Metadata::default(),
        };
        assert_eq!(s.n_bands(), 0);
        assert_eq!(s.wavelength_range(), None);
    }

    #[test]
    fn metadata_default_has_empty_strings() {
        let m = Metadata::default();
        assert!(m.material_name.is_empty());
        assert!(m.source_record_id.is_empty());
        assert!(m.license.is_empty());
        assert!(m.ingested_at.is_empty());
        assert!(m.adapter_version.is_empty());
    }
}
