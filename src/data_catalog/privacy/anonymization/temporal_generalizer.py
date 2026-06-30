"""Temporal data generalization to reduce re-identification risk."""

import pandas as pd


def generalize_to_year_month(series: pd.Series) -> pd.Series:
    """Generalizes date-like values to YYYY-MM format.

    Reduces temporal precision from day/time level to month level,
    significantly reducing re-identification risk when combined with
    spatial data. Values that cannot be parsed as dates are returned as-is.

    Args:
        series: Series containing date strings, datetime objects, or
            numeric timestamps (e.g. Excel-style days since 1899-12-30).

    Returns:
        Series of strings in YYYY-MM format for parseable values.
    """
    parsed = pd.to_datetime(series, errors="coerce")
    result = series.astype(str).copy()
    valid = parsed.notna()
    result[valid] = parsed[valid].dt.to_period("M").astype(str)
    return result


def drop_time_component(series: pd.Series) -> pd.Series:
    """Replaces time-of-day values with a coarse hour bucket (0, 6, 12, 18).

    Buckets: 00-05 → 0, 06-11 → 6, 12-17 → 12, 18-23 → 18.

    Args:
        series: Series of time strings in HH:MM:SS format.

    Returns:
        Series of integer hour buckets.
    """
    parsed = pd.to_datetime(series, format="%H:%M:%S", errors="coerce")
    valid = parsed.notna()
    result = series.copy()
    result[valid] = (parsed[valid].dt.hour // 6 * 6).astype(str)
    return result
