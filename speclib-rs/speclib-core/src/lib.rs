//! speclib-core: Core types and I/O for the speclib spectral library.

pub mod error;
pub mod id;
pub mod json;
pub mod matching;
pub mod parquet;
pub mod types;

pub use error::Error;
pub use matching::{match_spectrum, spectral_angle, MatchResult};
pub use types::{
    MaterialCategory, MeasurementType, Metadata, QualityFlag, SourceLibrary, Spectrum,
};
