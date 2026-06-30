"""Anonymization engine that routes columns to the appropriate technique."""

import pandas as pd

from data_catalog.agents.models import AnonAdvisoryReport
from data_catalog.privacy.anonymization.geohash_encoder import encode_to_h3
from data_catalog.privacy.anonymization.ip_masker import mask_last_octet
from data_catalog.privacy.anonymization.mac_hasher import hash_with_salt
from data_catalog.privacy.anonymization.temporal_generalizer import (
    drop_time_component,
    generalize_to_year_month,
)
from data_catalog.settings import settings

_H3_KEYWORDS = {"h3", "geohash", "hexagonal", "coordinate"}
_IP_KEYWORDS = {"ip", "octet"}
_MAC_KEYWORDS = {"sha", "hash", "salt", "mac"}
_DATE_KEYWORDS = {"date", "generali", "month", "year", "temporal"}
_TIME_KEYWORDS = {"time-of-day", "time_of_day", "hour", "time bucket"}


def anonymize(df: pd.DataFrame, report: AnonAdvisoryReport) -> pd.DataFrame:
    """Applies anonymization techniques to a DataFrame based on agent recommendations.

    Coordinate columns (lat/lon) are fused into a single ``h3_cell`` column
    and dropped from the result. All other PII columns are transformed in place.

    Args:
        df: Raw DataFrame containing PII columns.
        report: Anonymization advisory from ``analyze_dataset``.

    Returns:
        New DataFrame with PII columns anonymized. The original is not modified.
    """
    result = df.copy()
    result = _apply_h3(result, report)
    result = _apply_column_techniques(result, report)
    return result


def _apply_h3(df: pd.DataFrame, report: AnonAdvisoryReport) -> pd.DataFrame:
    h3_cols = [
        r.column_name
        for r in report.column_recommendations
        if any(kw in r.technique.lower() for kw in _H3_KEYWORDS) and r.column_name in df.columns
    ]

    lat_col = next((c for c in h3_cols if "lat" in c.lower()), None)
    lon_col = next((c for c in h3_cols if "lon" in c.lower() or "lng" in c.lower()), None)

    if lat_col and lon_col:
        df = df.copy()
        df["h3_cell"] = encode_to_h3(df[lat_col], df[lon_col], settings.h3_resolution)
        df = df.drop(columns=[lat_col, lon_col])

    return df


def _apply_column_techniques(df: pd.DataFrame, report: AnonAdvisoryReport) -> pd.DataFrame:
    for rec in report.column_recommendations:
        col = rec.column_name
        if col not in df.columns:
            continue

        technique = rec.technique.lower()

        if any(kw in technique for kw in _H3_KEYWORDS):
            continue
        if any(kw in technique for kw in _IP_KEYWORDS):
            df[col] = mask_last_octet(df[col])
        elif any(kw in technique for kw in _MAC_KEYWORDS):
            df[col] = hash_with_salt(df[col], settings.mac_hash_salt)
        elif any(kw in technique for kw in _TIME_KEYWORDS):
            df[col] = drop_time_component(df[col])
        elif any(kw in technique for kw in _DATE_KEYWORDS):
            df[col] = generalize_to_year_month(df[col])

    return df
