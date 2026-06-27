"""Low-level file readers for datasets with non-standard formats."""

from pathlib import Path

import pandas as pd

PLT_SKIP_ROWS = 6
PLT_COLUMNS = ["latitude", "longitude", "zero", "altitude_feet", "timestamp_days", "date", "time"]


def read_plt(path: Path, nrows: int | None = None) -> pd.DataFrame:
    """Reads a GeoLife .plt GPS trajectory file into a DataFrame.

    Args:
        path: Path to the ``.plt`` file.
        nrows: Optional row limit for sampling.

    Returns:
        DataFrame with named columns as defined in the GeoLife specification.
    """
    return pd.read_csv(
        path,
        skiprows=PLT_SKIP_ROWS,
        header=None,
        names=PLT_COLUMNS,
        nrows=nrows,
    )


def read_file(path: Path, nrows: int | None = None) -> pd.DataFrame:
    """Reads a CSV, Parquet or PLT file into a DataFrame.

    Args:
        path: Path to the file.
        nrows: Optional row limit. Ignored for Parquet.

    Returns:
        DataFrame with the file contents.
    """
    suffix = path.suffix.lower()

    if suffix == ".plt":
        return read_plt(path, nrows=nrows)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, nrows=nrows)
