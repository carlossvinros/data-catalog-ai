"""Calculates a privacy risk score based on detected PII fields."""

from data_catalog.profiling.pii_scanner import PIIScanResult, PIIType

_WEIGHTS: dict[PIIType, int] = {
    PIIType.COORDINATES: 40,
    PIIType.IDENTIFIER: 30,
    PIIType.IP_ADDRESS: 25,
    PIIType.MAC_ADDRESS: 25,
    PIIType.TEMPORAL: 20,
}


def calculate_risk_score(scan_result: PIIScanResult) -> int:
    """Calculates a privacy risk score from 0 (no risk) to 100 (maximum risk).

    Scores are additive per detected PII field and capped at 100.
    A dataset with coordinates + temporal data saturates the scale,
    reflecting the near-certain re-identification risk.

    Args:
        scan_result: Output of ``scan_pii``.

    Returns:
        Integer score between 0 and 100.
    """
    total = sum(_WEIGHTS.get(field.pii_type, 0) for field in scan_result.detected_fields)
    return min(total, 100)
