"""Detects personally identifiable information (PII) in dataset columns."""

from enum import StrEnum

from pydantic import BaseModel

from data_catalog.profiling.models import ColumnProfile, DatasetProfile


class PIIType(StrEnum):
    COORDINATES = "COORDINATES"
    TEMPORAL = "TEMPORAL"
    IDENTIFIER = "IDENTIFIER"
    IP_ADDRESS = "IP_ADDRESS"
    MAC_ADDRESS = "MAC_ADDRESS"


class LGPDClassification(StrEnum):
    SENSITIVE_PERSONAL = "Dado Pessoal Sensível"
    PERSONAL = "Dado Pessoal"
    DIRECT_IDENTIFIER = "Identificador Direto"
    REIDENTIFICATION_AMPLIFIER = "Amplificador de Re-identificação"


class PIIField(BaseModel):
    """A column identified as containing personal data.

    Attributes:
        column_name: Name of the column in the dataset.
        pii_type: Category of personal data detected.
        lgpd_classification: Classification under Brazilian LGPD.
    """

    column_name: str
    pii_type: PIIType
    lgpd_classification: LGPDClassification


class PIIScanResult(BaseModel):
    """Result of a PII scan over an entire dataset profile.

    Attributes:
        dataset_slug: Kaggle identifier of the scanned dataset.
        detected_fields: All PII fields found.
    """

    dataset_slug: str
    detected_fields: list[PIIField]

    @property
    def has_pii(self) -> bool:
        return len(self.detected_fields) > 0


_COORDINATE_NAMES = {"latitude", "longitude", "lat", "lon", "lng"}
_TEMPORAL_NAMES = {
    "date",
    "time",
    "timestamp",
    "datetime",
    "timestamp_days",
    "created_at",
    "updated_at",
}
_IDENTIFIER_NAMES = {"user_id", "userid", "uid", "device_id", "id"}
_IP_NAMES = {"ip", "ip_address", "ipaddress", "source_ip", "dest_ip"}
_MAC_NAMES = {"mac", "mac_address", "macaddress", "hardware_address"}


def scan_pii(profile: DatasetProfile) -> PIIScanResult:
    """Scans all columns in a dataset profile for PII signals.

    Args:
        profile: Statistical profile produced by ``extract_profile``.

    Returns:
        A ``PIIScanResult`` listing every detected PII field.
    """
    detected = [field for column in profile.columns for field in _detect_column_pii(column)]
    return PIIScanResult(dataset_slug=profile.dataset_slug, detected_fields=detected)


def _detect_column_pii(column: ColumnProfile) -> list[PIIField]:
    name = column.name.lower()
    detected: list[PIIField] = []

    if _is_coordinate(name, column):
        detected.append(
            PIIField(
                column_name=column.name,
                pii_type=PIIType.COORDINATES,
                lgpd_classification=LGPDClassification.SENSITIVE_PERSONAL,
            )
        )
    elif name in _TEMPORAL_NAMES:
        detected.append(
            PIIField(
                column_name=column.name,
                pii_type=PIIType.TEMPORAL,
                lgpd_classification=LGPDClassification.REIDENTIFICATION_AMPLIFIER,
            )
        )
    elif name in _IDENTIFIER_NAMES:
        detected.append(
            PIIField(
                column_name=column.name,
                pii_type=PIIType.IDENTIFIER,
                lgpd_classification=LGPDClassification.DIRECT_IDENTIFIER,
            )
        )
    elif name in _IP_NAMES:
        detected.append(
            PIIField(
                column_name=column.name,
                pii_type=PIIType.IP_ADDRESS,
                lgpd_classification=LGPDClassification.PERSONAL,
            )
        )
    elif name in _MAC_NAMES:
        detected.append(
            PIIField(
                column_name=column.name,
                pii_type=PIIType.MAC_ADDRESS,
                lgpd_classification=LGPDClassification.PERSONAL,
            )
        )

    return detected


def _is_coordinate(name: str, column: ColumnProfile) -> bool:
    if name not in _COORDINATE_NAMES:
        return False
    if column.min_value is None or column.max_value is None:
        return False
    if "lat" in name:
        return -90.0 <= column.min_value and column.max_value <= 90.0
    return -180.0 <= column.min_value and column.max_value <= 180.0
