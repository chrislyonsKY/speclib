"""speclib command-line interface.

Provides commands for ingestion, search, export, resampling,
static site building, and optional server startup.
"""

from __future__ import annotations

import logging

import click

logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def main() -> None:
    """Speclib — Federated spectral signature library."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@main.command()
@click.argument("source", type=click.Choice(["usgs", "ecostress", "aster", "emit"]))
@click.option("--config", type=click.Path(exists=True), help="Path to source YAML config.")
@click.option("--archive", default="speclib_archive.h5", help="HDF5 archive path.")
def ingest(source: str, config: str | None, archive: str) -> None:
    """Ingest spectra from an upstream source into the HDF5 archive."""
    # TODO: Resolve adapter from source name
    # TODO: Load config (default: data/upstream/{source}.yaml)
    # TODO: Run adapter.ingest_all()
    # TODO: Write spectra to HDF5 archive
    click.echo(f"TODO: Ingest from {source} → {archive}")


@main.command()
@click.argument("query")
@click.option("--category", help="Filter by material category.")
@click.option("--source", help="Filter by source library.")
@click.option("--quality", help="Minimum quality flag.")
@click.option("--archive", default="speclib_archive.h5", help="HDF5 archive path.")
def search(
    query: str, category: str | None, source: str | None, quality: str | None, archive: str
) -> None:
    """Search the spectral library."""
    # TODO: Load library from archive or Parquet
    # TODO: Apply search with filters
    # TODO: Print results table
    click.echo(f"TODO: Search '{query}' in {archive}")


@main.command()
@click.argument("spectrum_id")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "ascii", "esl", "sli", "specpr"]),
    default="json",
    help="Export format.",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
@click.option("--archive", default="speclib_archive.h5", help="HDF5 archive path.")
def export(spectrum_id: str, fmt: str, output: str | None, archive: str) -> None:
    """Export a spectrum to the specified format."""
    # TODO: Load spectrum from archive
    # TODO: Dispatch to exporter
    click.echo(f"TODO: Export {spectrum_id} as {fmt}")


@main.command()
@click.argument("spectrum_id")
@click.option("--sensor", required=True, help="Target sensor name or RSR YAML path.")
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
@click.option("--archive", default="speclib_archive.h5", help="HDF5 archive path.")
def resample(spectrum_id: str, sensor: str, output: str | None, archive: str) -> None:
    """Resample a spectrum to a target sensor's bands."""
    # TODO: Load spectrum
    # TODO: Run resampling engine
    # TODO: Output result
    click.echo(f"TODO: Resample {spectrum_id} → {sensor}")


@main.command()
@click.option("--archive", default="speclib_archive.h5", help="HDF5 archive path.")
@click.option("--parquet-dir", default="query/", help="Parquet output directory.")
@click.option("--static-dir", default="web/static/data/", help="Static JSON output directory.")
def build(archive: str, parquet_dir: str, static_dir: str) -> None:
    """Build Parquet query layer and static JSON catalog from HDF5 archive."""
    # TODO: HDF5 → Parquet
    # TODO: Parquet → Static JSON
    click.echo(f"TODO: Build {archive} → {parquet_dir} → {static_dir}")


@main.command()
@click.argument("spectrum_id")
@click.option("--archive", default="speclib_archive.h5", help="HDF5 archive path.")
def info(spectrum_id: str, archive: str) -> None:
    """Display metadata for a spectrum."""
    # TODO: Load and pretty-print metadata
    click.echo(f"TODO: Info for {spectrum_id}")


@main.command()
@click.option("--archive", default="speclib_archive.h5", help="HDF5 archive path.")
def stats(archive: str) -> None:
    """Show summary statistics for the library."""
    # TODO: Count by category, source, quality
    click.echo(f"TODO: Stats for {archive}")


@main.command()
@click.option("--host", default="127.0.0.1", help="Server host.")
@click.option("--port", default=8000, help="Server port.")
@click.option("--parquet-dir", default="query/", help="Parquet data directory.")
def serve(host: str, port: int, parquet_dir: str) -> None:
    """Start the optional FastAPI server."""
    # TODO: Import and run FastAPI app with uvicorn
    click.echo(f"TODO: Serve on {host}:{port}")


if __name__ == "__main__":
    main()
