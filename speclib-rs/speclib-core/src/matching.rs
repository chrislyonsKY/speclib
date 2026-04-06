//! Spectral matching algorithms for material identification.

use crate::error::Error;
use crate::types::Spectrum;

/// Result of matching a target spectrum against a library spectrum.
#[derive(Debug, Clone)]
pub struct MatchResult {
    /// Spectrum ID of the library match.
    pub spectrum_id: String,
    /// Name of the matched spectrum.
    pub name: String,
    /// Spectral angle in radians (0 = identical, π/2 = orthogonal).
    pub angle: f64,
}

/// Compute the spectral angle between two spectra in radians.
///
/// Both spectra must have identical wavelength grids. Returns an error
/// if wavelengths don't match or arrays are empty.
///
/// The spectral angle is the arc-cosine of the normalized dot product:
/// `SAM = acos( (a · b) / (|a| * |b|) )`
pub fn spectral_angle(a: &[f64], b: &[f64]) -> Result<f64, Error> {
    if a.len() != b.len() {
        return Err(Error::Validation(format!(
            "spectral angle requires equal-length arrays: {} vs {}",
            a.len(),
            b.len()
        )));
    }
    if a.is_empty() {
        return Err(Error::Validation(
            "spectral angle requires non-empty arrays".into(),
        ));
    }

    let dot: f64 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f64 = a.iter().map(|x| x * x).sum::<f64>().sqrt();
    let norm_b: f64 = b.iter().map(|x| x * x).sum::<f64>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        return Err(Error::Validation(
            "spectral angle undefined for zero vector".into(),
        ));
    }

    // Clamp to [-1, 1] to handle floating point imprecision
    let cos_angle = (dot / (norm_a * norm_b)).clamp(-1.0, 1.0);
    Ok(cos_angle.acos())
}

/// Match a target spectrum against a library of spectra.
///
/// Returns matches sorted by angle (best match first).
/// All library spectra must have the same wavelength grid as the target.
/// Spectra with mismatched wavelengths are skipped.
pub fn match_spectrum(target: &Spectrum, library: &[Spectrum]) -> Vec<MatchResult> {
    let mut results: Vec<MatchResult> = Vec::new();

    for lib_spec in library {
        if lib_spec.wavelengths.len() != target.wavelengths.len() {
            continue; // Skip mismatched wavelength grids
        }
        if let Ok(angle) = spectral_angle(&target.reflectance, &lib_spec.reflectance) {
            results.push(MatchResult {
                spectrum_id: lib_spec.spectrum_id.clone(),
                name: lib_spec.name.clone(),
                angle,
            });
        }
    }

    results.sort_by(|a, b| a.angle.partial_cmp(&b.angle).unwrap_or(std::cmp::Ordering::Equal));
    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identical_spectra_zero_angle() {
        let a = vec![0.1, 0.2, 0.3, 0.4, 0.5];
        let b = vec![0.1, 0.2, 0.3, 0.4, 0.5];
        let angle = spectral_angle(&a, &b).unwrap();
        assert!((angle - 0.0).abs() < 1e-10);
    }

    #[test]
    fn scaled_spectra_zero_angle() {
        // SAM is scale-invariant: 2*a should have angle 0 with a
        let a = vec![0.1, 0.2, 0.3, 0.4, 0.5];
        let b = vec![0.2, 0.4, 0.6, 0.8, 1.0];
        let angle = spectral_angle(&a, &b).unwrap();
        assert!((angle - 0.0).abs() < 1e-10);
    }

    #[test]
    fn orthogonal_spectra() {
        let a = vec![1.0, 0.0];
        let b = vec![0.0, 1.0];
        let angle = spectral_angle(&a, &b).unwrap();
        assert!((angle - std::f64::consts::FRAC_PI_2).abs() < 1e-10);
    }

    #[test]
    fn different_lengths_error() {
        let a = vec![0.1, 0.2, 0.3];
        let b = vec![0.1, 0.2];
        assert!(spectral_angle(&a, &b).is_err());
    }

    #[test]
    fn empty_arrays_error() {
        let a: Vec<f64> = vec![];
        let b: Vec<f64> = vec![];
        assert!(spectral_angle(&a, &b).is_err());
    }

    #[test]
    fn zero_vector_error() {
        let a = vec![0.0, 0.0, 0.0];
        let b = vec![0.1, 0.2, 0.3];
        assert!(spectral_angle(&a, &b).is_err());
    }

    #[test]
    fn match_spectrum_sorts_by_angle() {
        use crate::types::Metadata;

        let target = Spectrum {
            spectrum_id: "target".into(),
            name: "Target".into(),
            wavelengths: vec![0.4, 0.5, 0.6],
            reflectance: vec![0.1, 0.2, 0.3],
            errors: None,
            metadata: Metadata::default(),
        };

        let close = Spectrum {
            spectrum_id: "close".into(),
            name: "Close Match".into(),
            wavelengths: vec![0.4, 0.5, 0.6],
            reflectance: vec![0.11, 0.21, 0.31],
            errors: None,
            metadata: Metadata::default(),
        };

        let far = Spectrum {
            spectrum_id: "far".into(),
            name: "Far Match".into(),
            wavelengths: vec![0.4, 0.5, 0.6],
            reflectance: vec![0.3, 0.1, 0.05],
            errors: None,
            metadata: Metadata::default(),
        };

        let results = match_spectrum(&target, &[far.clone(), close.clone()]);
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].spectrum_id, "close"); // Best match first
        assert!(results[0].angle < results[1].angle);
    }

    #[test]
    fn match_spectrum_skips_mismatched_wavelengths() {
        use crate::types::Metadata;

        let target = Spectrum {
            spectrum_id: "target".into(),
            name: "Target".into(),
            wavelengths: vec![0.4, 0.5, 0.6],
            reflectance: vec![0.1, 0.2, 0.3],
            errors: None,
            metadata: Metadata::default(),
        };

        let different_grid = Spectrum {
            spectrum_id: "diff".into(),
            name: "Different Grid".into(),
            wavelengths: vec![0.4, 0.5],
            reflectance: vec![0.1, 0.2],
            errors: None,
            metadata: Metadata::default(),
        };

        let results = match_spectrum(&target, &[different_grid]);
        assert_eq!(results.len(), 0);
    }
}
