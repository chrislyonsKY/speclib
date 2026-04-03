# Coding Standards Guardrails

These rules apply to ALL code generated for this project, regardless of which agent is active.

## Python

- Target Python 3.11+ (use modern syntax: match/case, type unions with `|`, etc.)
- All scripts must use structured logging via `logging` module — no bare `print()` statements
- All functions must have docstrings (Google style) with parameters, returns, and raises
- All file paths must use `pathlib.Path` — never string concatenation for paths
- All I/O must use context managers (`with` statements)
- Error handling: explicit exception types, never bare `except:`
- Type hints on all function signatures (return type included)
- No pandas in core modules — use numpy for array operations, pyarrow for tabular
- `ruff` for linting, `ruff format` for formatting
- Import order: stdlib → third-party → local (enforced by ruff isort)

## JavaScript (D3.js / Web)

- ES6+ modules, no var declarations
- D3.js v7 — use selection.join() pattern, not enter/update/exit
- All chart dimensions derived from container, not hardcoded
- Accessible: ARIA labels on interactive elements, keyboard navigation for charts
- No external JS frameworks — vanilla JS + Plotly.js for charting (approved override of original D3.js-only constraint)

## Data Integrity

- Wavelength arrays must always be sorted ascending
- Reflectance values outside [0.0, 1.0] must be flagged, not silently clipped
- NaN/null handling: spectral gaps stored as NaN in arrays, documented in metadata
- All floating point comparisons use `numpy.isclose()` with documented tolerance
- Spectrum ID generation must be deterministic (same input → same ID)

## Testing

- pytest for all Python tests
- Tests organized to mirror src/ structure
- Each ingestion adapter has integration tests against sample data files
- Each export format has round-trip tests (write → read → compare)
- Spectral resampling validated against USGS reference convolved libraries
