# Contributing

Thank you for your interest in contributing to speclib.

## Development Setup

```bash
git clone https://github.com/chrislyonsKY/speclib.git
cd speclib
pip install -e ".[all]"
pre-commit install
```

## Code Standards

- Python 3.11+ with type hints on all function signatures
- Google-style docstrings
- `ruff` for linting and formatting
- `pathlib.Path` for all file operations
- `numpy` for spectral array operations (no pandas in core)

## Testing

```bash
pytest
pytest --cov=speclib --cov-report=term-missing
```

- Tests mirror the `src/` directory structure
- Ingestion adapters require integration tests against sample data
- Export formats require round-trip tests
- Spectral resampling must be validated against USGS references

## Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Write tests for new functionality
4. Ensure `ruff check` and `pytest` pass
5. Submit a pull request with a clear description

## Reporting Issues

Use [GitHub Issues](https://github.com/chrislyonsKY/speclib/issues) for bug reports and feature requests.

## License

By contributing, you agree that your contributions will be licensed under GPL-3.0-only.
