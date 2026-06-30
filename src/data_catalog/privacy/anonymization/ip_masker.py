"""IP address anonymization via last-octet zeroing."""

import ipaddress

import pandas as pd


def mask_last_octet(series: pd.Series) -> pd.Series:
    """Zeros the last octet of IPv4 addresses (e.g. 192.168.1.105 → 192.168.1.0).

    For IPv6 addresses, the value is returned unchanged as octet masking
    is not applicable to that format. Invalid values are passed through as-is.

    Args:
        series: Series of IP address strings.

    Returns:
        Series with last IPv4 octet replaced by zero.
    """
    return series.map(_mask_single)


def _mask_single(value: object) -> str:
    try:
        addr = ipaddress.ip_address(str(value))
        if addr.version == 4:
            network = str(addr).rsplit(".", 1)[0]
            return f"{network}.0"
        return str(addr)
    except ValueError:
        return str(value)
