"""Orchestrates the full ingestion pipeline for a Kaggle dataset."""

from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from data_catalog.ingestion.kaggle_client import KaggleDatasetClient
from data_catalog.ingestion.readers import read_file

console = Console()

_SUPPORTED_EXTENSIONS = {".csv", ".parquet", ".plt"}


@dataclass
class IngestionResult:
    """Outcome of a single dataset ingestion run.

    Attributes:
        dataset_slug: Kaggle identifier used for the run.
        destination: Local path where files were saved.
        files: List of files found after download.
        success: Whether the pipeline completed without errors.
        error: Error message if the pipeline failed, otherwise empty.
    """

    dataset_slug: str
    destination: Path
    files: list[Path] = field(default_factory=list)
    success: bool = False
    error: str = ""


def run_ingestion_pipeline(
    dataset_slug: str,
    client: KaggleDatasetClient | None = None,
) -> IngestionResult:
    """Downloads a Kaggle dataset and validates the result.

    Args:
        dataset_slug: Kaggle dataset identifier in ``owner/dataset-name`` format.
        client: Optional pre-configured ``KaggleDatasetClient``. A new instance
            is created automatically if not provided.

    Returns:
        An ``IngestionResult`` describing what was downloaded and whether
        the pipeline succeeded.
    """
    resolved_client = client or KaggleDatasetClient()
    result = IngestionResult(dataset_slug=dataset_slug, destination=Path())

    try:
        destination = resolved_client.download(dataset_slug)
        files = _collect_data_files(destination)
        _validate_sample(files)

        result.destination = destination
        result.files = files
        result.success = True

        console.print(f"[green]✔ Pipeline complete.[/green] {len(files)} file(s) ready.")

    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)
        console.print(f"[red]✖ Pipeline failed:[/red] {exc.__class__.__name__}: {exc}")

    return result


def _collect_data_files(directory: Path) -> list[Path]:
    """Returns all supported data files found recursively in ``directory``."""
    files = [f for f in directory.rglob("*") if f.suffix.lower() in _SUPPORTED_EXTENSIONS]

    if not files:
        raise FileNotFoundError(f"No data files found in {directory}")

    return sorted(files)


def _validate_sample(files: list[Path]) -> None:
    """Reads the first 5 rows of the first file to confirm it is parseable."""
    try:
        read_file(files[0], nrows=5)
    except Exception as exc:
        raise ValueError(f"Cannot read '{files[0].name}': {exc}") from exc
