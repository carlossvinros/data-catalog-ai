"""Pydantic models shared across the profiling pipeline."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ColumnProfile(BaseModel):
    """Statistical profile of a single dataset column.

    Attributes:
        name: Column name as it appears in the raw data.
        dtype: Pandas dtype string (e.g. ``float64``, ``object``).
        null_count: Number of null values.
        null_pct: Percentage of null values (0–100).
        unique_count: Number of distinct non-null values.
        min_value: Minimum numeric value, if applicable.
        max_value: Maximum numeric value, if applicable.
        sample_values: Up to 3 representative non-null values.
    """

    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    min_value: float | None = None
    max_value: float | None = None
    sample_values: list[Any] = []


class DatasetProfile(BaseModel):
    """Aggregated statistical profile of a dataset sample.

    Attributes:
        dataset_slug: Kaggle identifier of the source dataset.
        source_path: Local directory containing the raw files.
        total_files: Total number of data files discovered.
        sampled_files: Number of files actually read for profiling.
        total_rows: Total rows across all sampled files.
        columns: Per-column statistical profiles.
    """

    dataset_slug: str
    source_path: Path
    total_files: int
    sampled_files: int
    total_rows: int
    columns: list[ColumnProfile]
