//! Deterministic spectrum ID generation following format-spec §1.6.

use sha2::{Digest, Sha256};

/// Generate a deterministic spectrum ID from source metadata.
///
/// Format: `{source}_{category}_{slug}_{hash8}`
/// where slug is a lowercased, underscore-separated, 40-char-max version of the name,
/// and hash8 is the first 8 hex characters of a SHA-256 hash.
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
        let id1 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz.csv");
        let id2 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz.csv");
        assert_eq!(id1, id2);
    }

    #[test]
    fn format_correct() {
        let id = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz.csv");
        assert!(id.starts_with("ecostress_mineral_quartz_sio2_"));
        // Last 8 chars are hex
        let suffix = &id[id.len() - 8..];
        assert_eq!(suffix.len(), 8);
        assert!(suffix.chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn different_filenames_different_ids() {
        let id1 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz_a.csv");
        let id2 = generate_id("ECOSTRESS", "MINERAL", "Quartz SiO2", "quartz_b.csv");
        assert_ne!(id1, id2);
    }

    #[test]
    fn slug_truncated_to_40() {
        let long_name = "A very long material name that exceeds forty characters total";
        let id = generate_id("USGS_SPLIB07", "MINERAL", long_name, "file.txt");
        // Extract slug: between second and last underscore segments
        // Format: source_category_slug_hash8
        let parts: Vec<&str> = id.rsplitn(2, '_').collect();
        let hash_part = parts[0]; // last 8 hex chars
        assert_eq!(hash_part.len(), 8);
        // The slug portion (between "usgs_splib07_mineral_" prefix and "_hash8" suffix)
        let prefix = "usgs_splib07_mineral_";
        let slug_and_hash = &id[prefix.len()..];
        let slug = &slug_and_hash[..slug_and_hash.len() - 9]; // minus "_" + 8 hex
        assert!(slug.len() <= 40);
    }

    #[test]
    fn hash_is_hex() {
        let id = generate_id("KY_FIELD", "KY_INVASIVE", "Amur Honeysuckle", "amur.csv");
        let last8 = &id[id.len() - 8..];
        assert!(last8.chars().all(|c| c.is_ascii_hexdigit()));
    }
}
