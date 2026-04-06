# speclib-core

Core types and I/O for the [speclib](https://github.com/chrislyonsKY/speclib) federated spectral signature library.

[![Crates.io](https://img.shields.io/crates/v/speclib-core)](https://crates.io/crates/speclib-core)
[![License](https://img.shields.io/crates/l/speclib-core)](https://github.com/chrislyonsKY/speclib/blob/main/LICENSE)

## What is speclib?

An open spectral signature library with 5,900+ reference spectra from USGS, ECOSTRESS, and Kentucky field collections. Python, Rust, and R implementations share a common [format specification](https://github.com/chrislyonsKY/speclib/blob/main/docs/format-spec.md).

## Features

- **Core types** -- `Spectrum`, `Metadata`, and classification enums (`MaterialCategory`, `QualityFlag`, `SourceLibrary`, `MeasurementType`)
- **JSON I/O** -- Read and write individual spectrum files and catalog indexes
- **Parquet read** -- Read catalog and per-category spectra from the Parquet query layer
- **Spectral matching** -- Spectral Angle Mapper (SAM) with library matching
- **Cross-language ID generation** -- Deterministic spectrum IDs matching the Python implementation

## Quick start

```rust
use speclib_core::json::{read_catalog, read_spectrum};

// Read the catalog index
let catalog = read_catalog("data/catalog.json".as_ref())?;
println!("{} spectra in catalog", catalog.len());

// Read a single spectrum
let spectrum = read_spectrum("data/spectra/quartz.json".as_ref())?;
println!("{}: {} bands, {:.2}-{:.2} um",
    spectrum.name,
    spectrum.n_bands(),
    spectrum.wavelength_range().unwrap().0,
    spectrum.wavelength_range().unwrap().1,
);

// Spectral angle matching
use speclib_core::spectral_angle;
let angle = spectral_angle(&spectrum.reflectance, &other.reflectance)?;
println!("SAM angle: {:.4} rad", angle);
```

## Parquet support

```rust
use speclib_core::parquet::{read_catalog, read_spectra};

let catalog = read_catalog("query/catalog.parquet".as_ref())?;
let spectra = read_spectra("query/spectra/mineral.parquet".as_ref())?;
```

## Format specification

This crate implements the [speclib format specification v1.0](https://github.com/chrislyonsKY/speclib/blob/main/docs/format-spec.md), which defines the HDF5, Parquet, and JSON interchange formats shared across Python, Rust, and R.

## License

GPL-3.0-only
