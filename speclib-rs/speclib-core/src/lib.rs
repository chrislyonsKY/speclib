//! speclib-core: Core types and I/O for the speclib spectral library.

pub mod error;
pub mod id;
pub mod types;

pub use error::Error;
pub use types::{
    MaterialCategory, MeasurementType, Metadata, QualityFlag, SourceLibrary, Spectrum,
};
