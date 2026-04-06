//! Cross-language conformance tests.
//!
//! These tests read JSON files produced by the Python `build_reference.py` script.
//! They skip gracefully if the conformance fixtures are not present.

use std::path::PathBuf;

use speclib_core::json::{read_catalog, read_spectrum};

/// Locate the conformance JSON fixture directory, or `None` if absent.
fn conformance_json_dir() -> Option<PathBuf> {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest.parent()?.parent()?;
    let json_dir = repo_root
        .join("tests")
        .join("conformance")
        .join("reference")
        .join("json");
    if json_dir.exists() {
        Some(json_dir)
    } else {
        None
    }
}

#[test]
fn read_python_catalog() {
    let json_dir = match conformance_json_dir() {
        Some(d) => d,
        None => {
            println!("Skipping read_python_catalog: conformance fixtures not found");
            return;
        }
    };

    let catalog_path = json_dir.join("catalog.json");
    if !catalog_path.exists() {
        println!("Skipping read_python_catalog: catalog.json not found");
        return;
    }

    let entries = read_catalog(&catalog_path).expect("Failed to read catalog.json");
    assert!(!entries.is_empty(), "Catalog must contain at least one entry");

    for entry in &entries {
        assert!(
            !entry.spectrum_id.is_empty(),
            "spectrum_id must not be empty"
        );
        assert!(!entry.name.is_empty(), "name must not be empty");
        assert!(entry.n_bands > 0, "n_bands must be positive");
        assert!(
            entry.wavelength_min < entry.wavelength_max,
            "wavelength_min ({}) must be less than wavelength_max ({})",
            entry.wavelength_min,
            entry.wavelength_max
        );
    }
}

#[test]
fn read_python_spectra() {
    let json_dir = match conformance_json_dir() {
        Some(d) => d,
        None => {
            println!("Skipping read_python_spectra: conformance fixtures not found");
            return;
        }
    };

    let spectra_dir = json_dir.join("spectra");
    if !spectra_dir.exists() {
        println!("Skipping read_python_spectra: spectra/ directory not found");
        return;
    }

    let mut count = 0;
    for entry in std::fs::read_dir(&spectra_dir).expect("Failed to read spectra directory") {
        let entry = entry.expect("Failed to read directory entry");
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) != Some("json") {
            continue;
        }

        let spectrum =
            read_spectrum(&path).unwrap_or_else(|e| panic!("Failed to read {:?}: {}", path, e));

        assert!(
            !spectrum.wavelengths.is_empty(),
            "Spectrum {:?} has empty wavelengths",
            path
        );
        assert_eq!(
            spectrum.wavelengths.len(),
            spectrum.reflectance.len(),
            "Spectrum {:?}: wavelength/reflectance length mismatch",
            path
        );

        // Verify wavelengths are ascending
        for i in 1..spectrum.wavelengths.len() {
            assert!(
                spectrum.wavelengths[i] >= spectrum.wavelengths[i - 1],
                "Spectrum {:?}: wavelengths not ascending at index {}",
                path,
                i
            );
        }

        count += 1;
    }

    assert!(count > 0, "Expected at least one spectrum JSON file");
}
