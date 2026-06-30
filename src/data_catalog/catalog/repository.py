"""Repository: all database read/write operations for the catalog."""

from sqlalchemy import func, select

from data_catalog.agents.models import CatalogAnalysis
from data_catalog.catalog.database import get_session
from data_catalog.catalog.models import (
    AnonRecommendation,
    AuditRun,
    Dataset,
    DatasetColumn,
    PIIDetection,
)
from data_catalog.profiling.models import DatasetProfile
from data_catalog.profiling.pii_scanner import PIIScanResult


def save_analysis(
    profile: DatasetProfile,
    scan: PIIScanResult,
    risk_score: int,
    analysis: CatalogAnalysis,
) -> Dataset:
    """Persists a complete dataset analysis to the catalog.

    Applies an upsert strategy: if the dataset slug already exists, all
    related records are replaced with the latest analysis results.

    Args:
        profile: Statistical profile from ``extract_profile``.
        scan: PII scan result from ``scan_pii``.
        risk_score: Privacy risk score from ``calculate_risk_score``.
        analysis: Full agent analysis from ``analyze_dataset``.

    Returns:
        The persisted ``Dataset`` ORM instance.
    """
    with get_session() as session:
        dataset: Dataset | None = session.scalar(
            select(Dataset).where(Dataset.slug == profile.dataset_slug)
        )

        if dataset is None:
            dataset = Dataset(slug=profile.dataset_slug)
            session.add(dataset)

        dataset.domain = analysis.domain.domain
        dataset.total_files = profile.total_files
        dataset.total_rows = profile.total_rows
        dataset.sampled_files = profile.sampled_files
        dataset.risk_score = risk_score
        dataset.is_compliant = analysis.audit.is_compliant
        dataset.audit_summary = analysis.audit.summary

        dataset.columns = [
            DatasetColumn(
                name=col.name,
                dtype=col.dtype,
                null_pct=col.null_pct,
                unique_count=col.unique_count,
                min_value=col.min_value,
                max_value=col.max_value,
            )
            for col in profile.columns
        ]

        dataset.pii_detections = [
            PIIDetection(
                column_name=field.column_name,
                pii_type=field.pii_type,
                lgpd_classification=field.lgpd_classification,
            )
            for field in scan.detected_fields
        ]

        dataset.anon_recommendations = [
            AnonRecommendation(
                column_name=rec.column_name,
                technique=rec.technique,
                justification=rec.justification,
            )
            for rec in analysis.anonymization.column_recommendations
        ]

        dataset.audit_runs.append(
            AuditRun(
                audit_summary=analysis.audit.summary,
                violations=analysis.audit.violations,
                recommendations=analysis.audit.recommendations,
            )
        )

        session.commit()
        session.refresh(dataset)
        return dataset


def get_dataset(slug: str) -> Dataset | None:
    """Fetches a single dataset by its Kaggle slug.

    Args:
        slug: Kaggle identifier in ``owner/dataset-name`` format.

    Returns:
        The ``Dataset`` ORM instance, or ``None`` if not found.
    """
    with get_session() as session:
        result: Dataset | None = session.scalar(select(Dataset).where(Dataset.slug == slug))
        return result


def search_datasets(query: str) -> list[Dataset]:
    """Searches the catalog using PostgreSQL Full-Text Search.

    Args:
        query: Natural language search terms (e.g. ``"mobilidade GPS"``)

    Returns:
        List of matching ``Dataset`` instances ordered by relevance.
    """
    with get_session() as session:
        ts_query = func.plainto_tsquery("english", query)
        stmt = (
            select(Dataset)
            .where(Dataset.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(Dataset.search_vector, ts_query).desc())
        )
        return list(session.scalars(stmt).all())
