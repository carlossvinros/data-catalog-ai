"""Extracts statistical profiles from ingested datasets."""

import random
from pathlib import Path

import pandas as pd
from rich.console import Console

from data_catalog.ingestion.pipeline import IngestionResult
from data_catalog.ingestion.readers import read_file
from data_catalog.profiling.models import ColumnProfile, DatasetProfile

console = Console()

_DEFAULT_SAMPLE_SIZE = 50


def extract_profile(
    result: IngestionResult, sample_size: int = _DEFAULT_SAMPLE_SIZE
) -> DatasetProfile:
    """Builds a statistical profile from a random sample of the dataset files.

    Args:
        result: Completed ingestion result containing file paths.
        sample_size: Maximum number of files to read. Defaults to 50.

    Returns:
        A ``DatasetProfile`` with per-column statistics.
    """
    sampled_files = _sample_files(result.files, sample_size)
    df = _load_sample(sampled_files)

    console.print(
        f"[green]✔ Profile extracted.[/green] "
        f"{len(sampled_files)} files · {len(df):,} rows · {len(df.columns)} columns."
    )

    return DatasetProfile(
        dataset_slug=result.dataset_slug,
        source_path=result.destination,
        total_files=len(result.files),
        sampled_files=len(sampled_files),
        total_rows=len(df),
        columns=[_profile_column(df[col]) for col in df.columns],
    )


def _sample_files(files: list[Path], n: int) -> list[Path]:
    return random.sample(files, min(n, len(files)))


def _load_sample(files: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for path in files:
        try:
            frames.append(read_file(path))
        except Exception as exc:  # noqa: BLE001
            console.print(f"[yellow]⚠ Skipping {path.name}:[/yellow] {exc}")

    if not frames:
        raise RuntimeError("Could not read any file from the sample.")

    return pd.concat(frames, ignore_index=True)


def _profile_column(series: pd.Series) -> ColumnProfile:
    profile = ColumnProfile(
        name=str(series.name),
        dtype=str(series.dtype),
        null_count=int(series.isna().sum()),
        null_pct=round(float(series.isna().mean()) * 100, 2),
        unique_count=int(series.nunique()),
        sample_values=series.dropna().head(3).tolist(),
    )

    if pd.api.types.is_numeric_dtype(series):
        profile.min_value = float(series.min())
        profile.max_value = float(series.max())

    return profile
