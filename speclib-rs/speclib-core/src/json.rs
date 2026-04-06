//! JSON read/write for spectra and catalog index (format-spec §3).

use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::Error;
use crate::types::*;

// ---------------------------------------------------------------------------
// JSON structs
// ---------------------------------------------------------------------------

/// JSON representation of a single spectrum (format-spec §3.2).
#[derive(Debug, Serialize, Deserialize)]
pub struct SpectrumJson {
    pub spectrum_id: String,
    pub name: String,
    pub wavelengths: Vec<f64>,
    pub reflectance: Vec<f64>,
    pub metadata: SpectrumMetadataJson,
}

/// Metadata block within spectrum JSON.
#[derive(Debug, Serialize, Deserialize)]
pub struct SpectrumMetadataJson {
    #[serde(default)]
    pub material_category: String,
    #[serde(default)]
    pub source_library: String,
    #[serde(default)]
    pub quality: String,
    #[serde(default)]
    pub material_name: String,
    #[serde(default)]
    pub source_record_id: String,
    #[serde(default)]
    pub measurement_type: String,
    #[serde(default)]
    pub license: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub locality: String,
    #[serde(default)]
    pub citation: String,
}

/// Catalog entry (format-spec §3.1).
#[derive(Debug, Serialize, Deserialize)]
pub struct CatalogEntry {
    pub spectrum_id: String,
    pub name: String,
    #[serde(default)]
    pub material_category: String,
    #[serde(default)]
    pub source_library: String,
    #[serde(default)]
    pub quality: String,
    #[serde(default)]
    pub material_name: String,
    pub n_bands: usize,
    pub wavelength_min: f64,
    pub wavelength_max: f64,
    #[serde(default)]
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

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/// Convert a `Spectrum` to its JSON representation.
fn spectrum_to_json(spectrum: &Spectrum) -> SpectrumJson {
    let m = &spectrum.metadata;
    SpectrumJson {
        spectrum_id: spectrum.spectrum_id.clone(),
        name: spectrum.name.clone(),
        wavelengths: spectrum.wavelengths.clone(),
        reflectance: spectrum.reflectance.clone(),
        metadata: SpectrumMetadataJson {
            material_category: m.material_category.as_str().to_string(),
            source_library: m.source_library.as_str().to_string(),
            quality: m.quality.as_str().to_string(),
            material_name: m.material_name.clone(),
            source_record_id: m.source_record_id.clone(),
            measurement_type: m.measurement_type.as_str().to_string(),
            license: m.license.clone(),
            description: m.description.clone().unwrap_or_default(),
            locality: m.locality.clone().unwrap_or_default(),
            citation: m.citation.clone().unwrap_or_default(),
        },
    }
}

/// Convert a JSON representation back to a `Spectrum`.
fn spectrum_from_json(sj: SpectrumJson) -> Spectrum {
    let mj = sj.metadata;
    Spectrum {
        spectrum_id: sj.spectrum_id,
        name: sj.name,
        wavelengths: sj.wavelengths,
        reflectance: sj.reflectance,
        errors: None,
        metadata: Metadata {
            material_name: mj.material_name,
            material_category: mj.material_category.parse().unwrap_or_default(),
            material_subcategory: None,
            formula: None,
            source_library: mj.source_library.parse().unwrap_or_default(),
            source_record_id: mj.source_record_id,
            source_filename: None,
            instrument: None,
            measurement_type: mj.measurement_type.parse().unwrap_or_default(),
            measurement_date: None,
            grain_size: None,
            purity: None,
            xrd_results: None,
            em_results: None,
            description: if mj.description.is_empty() {
                None
            } else {
                Some(mj.description)
            },
            locality: if mj.locality.is_empty() {
                None
            } else {
                Some(mj.locality)
            },
            citation: if mj.citation.is_empty() {
                None
            } else {
                Some(mj.citation)
            },
            license: mj.license,
            quality: mj.quality.parse().unwrap_or_default(),
            ingested_at: String::new(),
            adapter_version: String::new(),
        },
    }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Read a single spectrum from a JSON file.
pub fn read_spectrum(path: &Path) -> Result<Spectrum, Error> {
    let data = fs::read_to_string(path)?;
    let sj: SpectrumJson = serde_json::from_str(&data)?;
    Ok(spectrum_from_json(sj))
}

/// Write a single spectrum to a JSON file.
pub fn write_spectrum(spectrum: &Spectrum, path: &Path) -> Result<(), Error> {
    let sj = spectrum_to_json(spectrum);
    let json = serde_json::to_string_pretty(&sj)?;
    fs::write(path, json)?;
    Ok(())
}

/// Read a catalog index from a JSON file.
pub fn read_catalog(path: &Path) -> Result<Vec<CatalogEntry>, Error> {
    let data = fs::read_to_string(path)?;
    let entries: Vec<CatalogEntry> = serde_json::from_str(&data)?;
    Ok(entries)
}

/// Write a catalog index to a JSON file.
pub fn write_catalog(entries: &[CatalogEntry], path: &Path) -> Result<(), Error> {
    let json = serde_json::to_string_pretty(&entries)?;
    fs::write(path, json)?;
    Ok(())
}

/// Build a `CatalogEntry` from a `Spectrum`.
pub fn catalog_entry_from_spectrum(spectrum: &Spectrum) -> CatalogEntry {
    let m = &spectrum.metadata;
    let (wl_min, wl_max) = spectrum.wavelength_range().unwrap_or((0.0, 0.0));
    CatalogEntry {
        spectrum_id: spectrum.spectrum_id.clone(),
        name: spectrum.name.clone(),
        material_category: m.material_category.as_str().to_string(),
        source_library: m.source_library.as_str().to_string(),
        quality: m.quality.as_str().to_string(),
        material_name: m.material_name.clone(),
        n_bands: spectrum.n_bands(),
        wavelength_min: wl_min,
        wavelength_max: wl_max,
        license: m.license.clone(),
        citation: m.citation.clone().unwrap_or_default(),
        instrument: m.instrument.clone().unwrap_or_default(),
        locality: m.locality.clone().unwrap_or_default(),
        measurement_type: m.measurement_type.as_str().to_string(),
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn sample_spectrum() -> Spectrum {
        Spectrum {
            spectrum_id: "ecostress_mineral_quartz_sio2_abcd1234".into(),
            name: "Quartz SiO2".into(),
            wavelengths: vec![0.4, 0.5, 0.6, 0.7, 0.8],
            reflectance: vec![0.12, 0.25, 0.37, 0.41, 0.45],
            errors: None,
            metadata: Metadata {
                material_name: "Quartz SiO2".into(),
                material_category: MaterialCategory::Mineral,
                material_subcategory: None,
                formula: Some("SiO2".into()),
                source_library: SourceLibrary::Ecostress,
                source_record_id: "eco_quartz_001".into(),
                source_filename: Some("quartz.csv".into()),
                instrument: Some("ASD FieldSpec".into()),
                measurement_type: MeasurementType::Laboratory,
                measurement_date: None,
                grain_size: None,
                purity: None,
                xrd_results: None,
                em_results: None,
                description: Some("Test quartz spectrum".into()),
                locality: Some("Narsarsuk, Greenland".into()),
                citation: Some("Test citation".into()),
                license: "CC0 / Public Domain".into(),
                quality: QualityFlag::Good,
                ingested_at: "2025-01-01T00:00:00Z".into(),
                adapter_version: "0.1.0".into(),
            },
        }
    }

    #[test]
    fn write_read_spectrum_roundtrip() {
        let tmp = TempDir::new().unwrap();
        let path = tmp.path().join("spectrum.json");
        let original = sample_spectrum();

        write_spectrum(&original, &path).unwrap();
        let loaded = read_spectrum(&path).unwrap();

        assert_eq!(loaded.spectrum_id, original.spectrum_id);
        assert_eq!(loaded.name, original.name);
        assert_eq!(loaded.wavelengths, original.wavelengths);
        assert_eq!(loaded.reflectance, original.reflectance);
        assert_eq!(loaded.metadata.material_name, original.metadata.material_name);
        assert_eq!(loaded.metadata.material_category, original.metadata.material_category);
        assert_eq!(loaded.metadata.source_library, original.metadata.source_library);
        assert_eq!(loaded.metadata.quality, original.metadata.quality);
        assert_eq!(loaded.metadata.measurement_type, original.metadata.measurement_type);
        assert_eq!(loaded.metadata.license, original.metadata.license);
        assert_eq!(loaded.metadata.locality, original.metadata.locality);
        assert_eq!(loaded.metadata.citation, original.metadata.citation);
        assert_eq!(loaded.metadata.description, original.metadata.description);
    }

    #[test]
    fn write_read_catalog_roundtrip() {
        let tmp = TempDir::new().unwrap();
        let path = tmp.path().join("catalog.json");

        let entries = vec![
            CatalogEntry {
                spectrum_id: "eco_mineral_quartz_abcd1234".into(),
                name: "Quartz".into(),
                material_category: "MINERAL".into(),
                source_library: "ECOSTRESS".into(),
                quality: "GOOD".into(),
                material_name: "Quartz SiO2".into(),
                n_bands: 480,
                wavelength_min: 0.4,
                wavelength_max: 2.5,
                license: "CC0".into(),
                citation: "Test".into(),
                instrument: "ASD".into(),
                locality: "Greenland".into(),
                measurement_type: "LABORATORY".into(),
            },
            CatalogEntry {
                spectrum_id: "ky_vegetation_honeysuckle_ef567890".into(),
                name: "Amur Honeysuckle".into(),
                material_category: "KY_INVASIVE".into(),
                source_library: "KY_FIELD".into(),
                quality: "VERIFIED".into(),
                material_name: "Lonicera maackii".into(),
                n_bands: 2151,
                wavelength_min: 0.35,
                wavelength_max: 2.5,
                license: "CC-BY-4.0".into(),
                citation: "Lyons et al. 2024".into(),
                instrument: "SVC HR-1024i".into(),
                locality: "Lexington, KY".into(),
                measurement_type: "FIELD".into(),
            },
        ];

        write_catalog(&entries, &path).unwrap();
        let loaded = read_catalog(&path).unwrap();

        assert_eq!(loaded.len(), 2);
        assert_eq!(loaded[0].spectrum_id, entries[0].spectrum_id);
        assert_eq!(loaded[0].n_bands, 480);
        assert_eq!(loaded[1].spectrum_id, entries[1].spectrum_id);
        assert_eq!(loaded[1].material_category, "KY_INVASIVE");
        assert_eq!(loaded[1].wavelength_max, 2.5);
    }

    #[test]
    fn catalog_entry_from_spectrum_fields() {
        let spectrum = sample_spectrum();
        let entry = catalog_entry_from_spectrum(&spectrum);

        assert_eq!(entry.spectrum_id, spectrum.spectrum_id);
        assert_eq!(entry.name, spectrum.name);
        assert_eq!(entry.material_category, "MINERAL");
        assert_eq!(entry.source_library, "ECOSTRESS");
        assert_eq!(entry.quality, "GOOD");
        assert_eq!(entry.measurement_type, "LABORATORY");
        assert_eq!(entry.n_bands, 5);
        assert!((entry.wavelength_min - 0.4).abs() < 1e-10);
        assert!((entry.wavelength_max - 0.8).abs() < 1e-10);
        assert_eq!(entry.license, "CC0 / Public Domain");
    }

    #[test]
    fn read_spectrum_from_python_output() {
        let json_str = r#"{
  "spectrum_id": "ecostress_mineral_acmite_a1895d08",
  "name": "Acmite NaFe+3 Si2O6",
  "wavelengths": [2.0795, 2.0803, 2.0812],
  "reflectance": [0.1234, 0.2345, 0.3456],
  "metadata": {
    "material_category": "MINERAL",
    "source_library": "ECOSTRESS",
    "quality": "GOOD",
    "material_name": "Acmite NaFe+3 Si2O6",
    "source_record_id": "eco_acmite_001",
    "measurement_type": "LABORATORY",
    "license": "CC0 / Public Domain",
    "description": "Acmite from Narsarsuk",
    "locality": "Narsarsuk, Greenland",
    "citation": "Meerdink et al. 2019"
  }
}"#;

        let sj: SpectrumJson = serde_json::from_str(json_str).unwrap();
        let spectrum = spectrum_from_json(sj);

        assert_eq!(spectrum.spectrum_id, "ecostress_mineral_acmite_a1895d08");
        assert_eq!(spectrum.name, "Acmite NaFe+3 Si2O6");
        assert_eq!(spectrum.wavelengths.len(), 3);
        assert_eq!(spectrum.reflectance.len(), 3);
        assert_eq!(spectrum.metadata.material_category, MaterialCategory::Mineral);
        assert_eq!(spectrum.metadata.source_library, SourceLibrary::Ecostress);
        assert_eq!(spectrum.metadata.quality, QualityFlag::Good);
        assert_eq!(spectrum.metadata.measurement_type, MeasurementType::Laboratory);
        assert_eq!(spectrum.metadata.license, "CC0 / Public Domain");
        assert_eq!(
            spectrum.metadata.locality,
            Some("Narsarsuk, Greenland".to_string())
        );
    }
}
