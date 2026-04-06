# speclib-cli

Command-line interface for the [speclib](https://github.com/chrislyonsKY/speclib) spectral signature library.

[![Crates.io](https://img.shields.io/crates/v/speclib-cli)](https://crates.io/crates/speclib-cli)
[![License](https://img.shields.io/crates/l/speclib-cli)](https://github.com/chrislyonsKY/speclib/blob/main/LICENSE)

## Install

```bash
cargo install speclib-cli
```

## Commands

```bash
# Show archive info -- spectrum counts by category
speclib info catalog.json

# Search by name (works with JSON or Parquet catalogs)
speclib search "quartz" --catalog catalog.parquet
speclib search "honeysuckle" --catalog catalog.json --category KY_INVASIVE

# Export a spectrum as JSON
speclib export ecostress_mineral_quartz_sio2_abc12345 --dir data/

# Match a spectrum against the library (Spectral Angle Mapper)
speclib match target.json --dir data/ --top 10
```

## Data

Download spectral data from the [speclib viewer](https://chrislyonsKY.github.io/speclib/) or build from source using the Python package.

## License

GPL-3.0-only
