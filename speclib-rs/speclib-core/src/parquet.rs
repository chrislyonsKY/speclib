//! Parquet I/O for the speclib query layer (format-spec S2).

use std::fs::File;
use std::path::Path;

use arrow::array::{Array, AsArray};
use arrow::datatypes::{Float64Type, Int64Type};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;

use crate::error::Error;
use crate::json::CatalogEntry;
use crate::types::{Metadata, Spectrum};

/// Read catalog entries from a `catalog.parquet` file.
///
/// Extracts all columns defined in the format spec (spectrum_id, name,
/// material_category, source_library, quality, material_name, n_bands,
/// wavelength_min, wavelength_max, license, citation, instrument, locality).
pub fn read_catalog(path: &Path) -> Result<Vec<CatalogEntry>, Error> {
    let file = File::open(path)?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
    let reader = builder.build()?;

    let mut entries = Vec::new();

    for batch_result in reader {
        let batch = batch_result?;
        let num_rows = batch.num_rows();
        let schema = batch.schema();

        // Resolve column indices by name for robustness.
        let col_idx = |name: &str| -> Option<usize> {
            schema.fields().iter().position(|f| f.name() == name)
        };

        let spectrum_id_idx = col_idx("spectrum_id");
        let name_idx = col_idx("name");
        let material_category_idx = col_idx("material_category");
        let source_library_idx = col_idx("source_library");
        let quality_idx = col_idx("quality");
        let material_name_idx = col_idx("material_name");
        let n_bands_idx = col_idx("n_bands");
        let wavelength_min_idx = col_idx("wavelength_min");
        let wavelength_max_idx = col_idx("wavelength_max");
        let license_idx = col_idx("license");
        let citation_idx = col_idx("citation");
        let instrument_idx = col_idx("instrument");
        let locality_idx = col_idx("locality");

        for row in 0..num_rows {
            let get_str = |idx: Option<usize>| -> String {
                idx.map(|i| {
                    let arr = batch.column(i).as_string::<i32>();
                    if arr.is_null(row) {
                        String::new()
                    } else {
                        arr.value(row).to_string()
                    }
                })
                .unwrap_or_default()
            };

            let n_bands = n_bands_idx
                .map(|i| {
                    let arr = batch.column(i).as_primitive::<Int64Type>();
                    arr.value(row) as usize
                })
                .unwrap_or(0);

            let wavelength_min = wavelength_min_idx
                .map(|i| {
                    let arr = batch.column(i).as_primitive::<Float64Type>();
                    arr.value(row)
                })
                .unwrap_or(0.0);

            let wavelength_max = wavelength_max_idx
                .map(|i| {
                    let arr = batch.column(i).as_primitive::<Float64Type>();
                    arr.value(row)
                })
                .unwrap_or(0.0);

            entries.push(CatalogEntry {
                spectrum_id: get_str(spectrum_id_idx),
                name: get_str(name_idx),
                material_category: get_str(material_category_idx),
                source_library: get_str(source_library_idx),
                quality: get_str(quality_idx),
                material_name: get_str(material_name_idx),
                n_bands,
                wavelength_min,
                wavelength_max,
                license: get_str(license_idx),
                citation: get_str(citation_idx),
                instrument: get_str(instrument_idx),
                locality: get_str(locality_idx),
                // measurement_type is not present in catalog.parquet
                measurement_type: String::new(),
            });
        }
    }

    Ok(entries)
}

/// Read spectra from a per-category Parquet file (`spectra/{category}.parquet`).
///
/// The Parquet files contain only spectrum_id, name, wavelengths, and
/// reflectance columns.  A minimal `Spectrum` is returned with default
/// `Metadata` -- the caller should enrich from the catalog if needed.
pub fn read_spectra(path: &Path) -> Result<Vec<Spectrum>, Error> {
    let file = File::open(path)?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)?;
    let reader = builder.build()?;

    let mut spectra = Vec::new();

    for batch_result in reader {
        let batch = batch_result?;
        let num_rows = batch.num_rows();
        let schema = batch.schema();

        let col_idx = |name: &str| -> Option<usize> {
            schema.fields().iter().position(|f| f.name() == name)
        };

        let spectrum_id_idx = col_idx("spectrum_id");
        let name_idx = col_idx("name");
        let wavelengths_idx = col_idx("wavelengths");
        let reflectance_idx = col_idx("reflectance");

        for row in 0..num_rows {
            let get_str = |idx: Option<usize>| -> String {
                idx.map(|i| {
                    let arr = batch.column(i).as_string::<i32>();
                    if arr.is_null(row) {
                        String::new()
                    } else {
                        arr.value(row).to_string()
                    }
                })
                .unwrap_or_default()
            };

            let wavelengths = wavelengths_idx
                .map(|i| {
                    let list_arr = batch.column(i).as_list::<i32>();
                    let inner = list_arr.value(row);
                    inner.as_primitive::<Float64Type>().values().to_vec()
                })
                .unwrap_or_default();

            let reflectance = reflectance_idx
                .map(|i| {
                    let list_arr = batch.column(i).as_list::<i32>();
                    let inner = list_arr.value(row);
                    inner.as_primitive::<Float64Type>().values().to_vec()
                })
                .unwrap_or_default();

            spectra.push(Spectrum {
                spectrum_id: get_str(spectrum_id_idx),
                name: get_str(name_idx),
                wavelengths,
                reflectance,
                errors: None,
                metadata: Metadata::default(),
            });
        }
    }

    Ok(spectra)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    /// Resolve the conformance fixtures directory.
    fn conformance_parquet_dir() -> PathBuf {
        let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        // speclib-rs/speclib-core -> speclib-rs -> speclib (repo root)
        manifest
            .parent()
            .unwrap()
            .parent()
            .unwrap()
            .join("tests")
            .join("conformance")
            .join("reference")
            .join("parquet")
    }

    #[test]
    fn read_catalog_from_conformance() {
        let dir = conformance_parquet_dir();
        let catalog_path = dir.join("catalog.parquet");
        if !catalog_path.exists() {
            eprintln!("Skipping: conformance fixture not found at {catalog_path:?}");
            return;
        }

        let entries = read_catalog(&catalog_path).expect("failed to read catalog.parquet");
        assert!(!entries.is_empty(), "catalog should contain entries");

        // Spot-check the first entry has required fields populated.
        let first = &entries[0];
        assert!(
            !first.spectrum_id.is_empty(),
            "spectrum_id should not be empty"
        );
        assert!(!first.name.is_empty(), "name should not be empty");
        assert!(first.n_bands > 0, "n_bands should be positive");
        assert!(
            first.wavelength_min < first.wavelength_max,
            "wavelength_min should be less than wavelength_max"
        );
    }

    #[test]
    fn read_spectra_from_conformance() {
        let dir = conformance_parquet_dir();
        let spectra_dir = dir.join("spectra");
        if !spectra_dir.exists() {
            eprintln!("Skipping: conformance spectra dir not found at {spectra_dir:?}");
            return;
        }

        // Find the first available category Parquet file.
        let parquet_file = std::fs::read_dir(&spectra_dir)
            .expect("failed to read spectra dir")
            .filter_map(|e| e.ok())
            .find(|e| {
                e.path()
                    .extension()
                    .is_some_and(|ext| ext == "parquet")
            });

        let parquet_file = match parquet_file {
            Some(f) => f.path(),
            None => {
                eprintln!("Skipping: no parquet files found in {spectra_dir:?}");
                return;
            }
        };

        let spectra =
            read_spectra(&parquet_file).expect("failed to read spectra parquet");
        assert!(!spectra.is_empty(), "spectra file should contain entries");

        let first = &spectra[0];
        assert!(
            !first.spectrum_id.is_empty(),
            "spectrum_id should not be empty"
        );
        assert!(
            !first.wavelengths.is_empty(),
            "wavelengths should not be empty"
        );
        assert!(
            !first.reflectance.is_empty(),
            "reflectance should not be empty"
        );
        assert_eq!(
            first.wavelengths.len(),
            first.reflectance.len(),
            "wavelengths and reflectance must have equal length"
        );
    }
}
