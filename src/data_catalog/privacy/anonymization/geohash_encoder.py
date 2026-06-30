"""H3 hexagonal geospatial encoding for coordinate anonymization."""

import h3
import pandas as pd


def encode_to_h3(lat: pd.Series, lon: pd.Series, resolution: int = 7) -> pd.Series:
    """Encodes latitude/longitude pairs into H3 hexagonal cell identifiers.

    At resolution 7, each hexagon covers approximately 150m radius,
    preventing exact location recovery while preserving spatial utility
    for density analysis and mobility pattern detection.

    Args:
        lat: Series of latitude values (range -90 to 90).
        lon: Series of longitude values (range -180 to 180).
        resolution: H3 resolution level (0=coarse, 15=fine). Defaults to 7.

    Returns:
        Series of H3 cell ID strings, indexed identically to ``lat``.
    """
    cells = [h3.latlng_to_cell(la, lo, resolution) for la, lo in zip(lat, lon, strict=False)]
    return pd.Series(cells, index=lat.index, name="h3_cell")
