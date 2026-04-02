# Contributing to speclib

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes following the conventions in [CLAUDE.md](CLAUDE.md)
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   `feat(module): description`
5. Push and open a pull request against `main`

## Development Setup

```bash
git clone https://github.com/chrislyonsKY/speclib.git
cd speclib
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```

## Code Standards

- Follow the conventions defined in CLAUDE.md and `ai-dev/guardrails/coding-standards.md`
- All code must include error handling, logging, and docstrings
- Run `ruff check .` and `ruff format .` before submitting
- Run `pytest` and ensure all tests pass

## Adding a New Ingestion Adapter

1. Create `src/speclib/ingest/yoursource.py` inheriting from `BaseAdapter`
2. Add a YAML config in `data/upstream/yoursource.yaml`
3. Register the adapter in the CLI
4. Add integration tests with sample data files

## Reporting Bugs

Open a GitHub Issue with:
- A clear title
- Steps to reproduce
- Expected vs. actual behavior
- Python version and OS

## Security Vulnerabilities

Do not open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md).

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
