"""MAC address and identifier anonymization via salted SHA-256 hashing."""

import hashlib

import pandas as pd


def hash_with_salt(series: pd.Series, salt: str) -> pd.Series:
    """Hashes each value with SHA-256 using a project-specific salt.

    The salt prevents rainbow table attacks: even if an attacker knows
    every possible MAC address, they cannot reverse the hash without
    knowing the salt. The digest is truncated to 8 hex characters for
    readability while maintaining sufficient collision resistance.

    Args:
        series: Series of MAC addresses or identifier strings.
        salt: Secret salt loaded from ``MAC_HASH_SALT`` in the environment.

    Returns:
        Series of 8-character hex digests.
    """
    return series.map(lambda value: _hash_single(str(value), salt))


def _hash_single(value: str, salt: str) -> str:
    payload = f"{salt}{value}".encode()
    return hashlib.sha256(payload).hexdigest()[:8]
