//! speclib CLI — search, inspect, and export spectral library data.

use std::path::{Path, PathBuf};
use std::process;

use clap::{Parser, Subcommand};

/// speclib — Federated Spectral Signature Library
#[derive(Parser)]
#[command(name = "speclib", version, about)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Show archive info — spectrum counts by category
    Info {
        /// Path to catalog.json or catalog.parquet
        path: PathBuf,
    },
    /// Search the catalog by name
    Search {
        /// Search query (matched against spectrum name)
        query: String,
        /// Path to catalog.json or catalog.parquet
        #[arg(long)]
        catalog: PathBuf,
        /// Filter by material category
        #[arg(long)]
        category: Option<String>,
    },
    /// Export a single spectrum to JSON
    Export {
        /// Spectrum ID to export
        spectrum_id: String,
        /// Directory containing spectra/ JSON files
        #[arg(long)]
        dir: PathBuf,
    },
    /// Match a spectrum against library spectra
    Match {
        /// Path to target spectrum JSON file
        target: PathBuf,
        /// Path to library spectra parquet or JSON directory
        #[arg(long)]
        dir: PathBuf,
        /// Number of top matches to show
        #[arg(long, default_value = "5")]
        top: usize,
    },
}

fn main() {
    let cli = Cli::parse();

    let result = match cli.command {
        Commands::Info { path } => cmd_info(&path),
        Commands::Search {
            query,
            catalog,
            category,
        } => cmd_search(&query, &catalog, category.as_deref()),
        Commands::Export { spectrum_id, dir } => cmd_export(&spectrum_id, &dir),
        Commands::Match { target, dir, top } => cmd_match(&target, &dir, top),
    };

    if let Err(e) = result {
        eprintln!("Error: {e}");
        process::exit(1);
    }
}

fn cmd_info(path: &Path) -> Result<(), speclib_core::Error> {
    let entries = if path.extension().is_some_and(|e| e == "parquet") {
        speclib_core::parquet::read_catalog(path)?
    } else {
        speclib_core::json::read_catalog(path)?
    };

    println!("Catalog: {} spectra", entries.len());

    // Count by category
    let mut counts: std::collections::BTreeMap<String, usize> = std::collections::BTreeMap::new();
    for entry in &entries {
        *counts.entry(entry.material_category.clone()).or_default() += 1;
    }
    for (cat, count) in &counts {
        println!("  {cat}: {count}");
    }
    Ok(())
}

fn cmd_search(
    query: &str,
    catalog: &Path,
    category: Option<&str>,
) -> Result<(), speclib_core::Error> {
    let entries = if catalog.extension().is_some_and(|e| e == "parquet") {
        speclib_core::parquet::read_catalog(catalog)?
    } else {
        speclib_core::json::read_catalog(catalog)?
    };

    let query_lower = query.to_lowercase();
    let mut matches: Vec<_> = entries
        .iter()
        .filter(|e| {
            let name_match = e.name.to_lowercase().contains(&query_lower)
                || e.material_name.to_lowercase().contains(&query_lower);
            let cat_match = category
                .map(|c| e.material_category.eq_ignore_ascii_case(c))
                .unwrap_or(true);
            name_match && cat_match
        })
        .collect();

    matches.sort_by(|a, b| a.name.cmp(&b.name));

    if matches.is_empty() {
        println!("No matches found for \"{query}\"");
    } else {
        println!("{} match(es) for \"{}\":\n", matches.len(), query);
        for m in &matches {
            println!(
                "  {} — {} [{}, {} bands, {:.2}–{:.2} µm]",
                m.spectrum_id,
                m.name,
                m.material_category,
                m.n_bands,
                m.wavelength_min,
                m.wavelength_max
            );
        }
    }
    Ok(())
}

fn cmd_export(spectrum_id: &str, dir: &Path) -> Result<(), speclib_core::Error> {
    let spectra_dir = dir.join("spectra");
    let path = spectra_dir.join(format!("{spectrum_id}.json"));

    if !path.exists() {
        return Err(speclib_core::Error::Io(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Spectrum not found: {}", path.display()),
        )));
    }

    let spectrum = speclib_core::json::read_spectrum(&path)?;
    let json = serde_json::to_string_pretty(&spectrum)?;
    println!("{json}");
    Ok(())
}

fn cmd_match(target_path: &Path, dir: &Path, top: usize) -> Result<(), speclib_core::Error> {
    let target = speclib_core::json::read_spectrum(target_path)?;

    // Load all spectra from JSON directory
    let spectra_dir = dir.join("spectra");
    if !spectra_dir.exists() {
        return Err(speclib_core::Error::Io(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Spectra directory not found: {}", spectra_dir.display()),
        )));
    }

    let mut library: Vec<speclib_core::Spectrum> = Vec::new();
    for entry in std::fs::read_dir(&spectra_dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.extension().is_some_and(|e| e == "json")
            && let Ok(spec) = speclib_core::json::read_spectrum(&path)
        {
            library.push(spec);
        }
    }

    let results = speclib_core::match_spectrum(&target, &library);

    if results.is_empty() {
        println!("No matches found (no spectra with matching wavelength grid)");
    } else {
        let n = top.min(results.len());
        println!("Top {} match(es) for \"{}\":\n", n, target.name);
        for m in &results[..n] {
            println!("  {:.4} rad — {} ({})", m.angle, m.name, m.spectrum_id);
        }
    }
    Ok(())
}
