"""Pydantic output models for each AI agent in the catalog pipeline."""

from typing import Literal

from pydantic import BaseModel, Field


class LGPDAuditReport(BaseModel):
    """LGPD compliance audit produced by the AuditAgent.

    Attributes:
        is_compliant: Whether the dataset meets minimum LGPD requirements.
        violations: List of specific compliance violations found.
        recommendations: Actionable steps to achieve compliance.
        summary: One-paragraph executive summary of the audit.
    """

    is_compliant: bool
    violations: list[str]
    recommendations: list[str]
    summary: str


class DomainClassification(BaseModel):
    """Dataset domain classification produced by the CategorizerAgent.

    Attributes:
        domain: Primary domain category of the dataset.
        confidence: Confidence score between 0.0 and 1.0.
        justification: Brief explanation of the classification decision.
    """

    domain: Literal["Mobility", "Telecom", "Logistics", "Healthcare", "Finance", "Other"]
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str


class ColumnAnonRecommendation(BaseModel):
    """Anonymization recommendation for a single PII column.

    Attributes:
        column_name: Name of the column requiring anonymization.
        technique: Specific anonymization technique to apply.
        justification: Why this technique is appropriate for this column.
    """

    column_name: str
    technique: str
    justification: str


class AnonAdvisoryReport(BaseModel):
    """Anonymization advisory produced by the AnonAdvisorAgent.

    Attributes:
        column_recommendations: Per-column anonymization recommendations.
        priority_columns: Columns that must be anonymized first, ordered by risk.
    """

    column_recommendations: list[ColumnAnonRecommendation]
    priority_columns: list[str]


class CatalogAnalysis(BaseModel):
    """Aggregated analysis of a dataset produced by the full agent crew.

    Attributes:
        dataset_slug: Kaggle identifier of the analyzed dataset.
        risk_score: Privacy risk score from 0 (no risk) to 100 (maximum risk).
        audit: LGPD compliance audit report.
        domain: Dataset domain classification.
        anonymization: Per-column anonymization advisory.
    """

    dataset_slug: str
    risk_score: int = Field(ge=0, le=100)
    audit: LGPDAuditReport
    domain: DomainClassification
    anonymization: AnonAdvisoryReport
