"""AI agent crew for dataset cataloging, LGPD auditing, and anonymization advisory."""

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from rich.console import Console

from data_catalog.agents.models import (
    AnonAdvisoryReport,
    CatalogAnalysis,
    DomainClassification,
    LGPDAuditReport,
)
from data_catalog.profiling.models import DatasetProfile
from data_catalog.profiling.pii_scanner import PIIScanResult
from data_catalog.settings import settings

console = Console()

_provider = GoogleProvider(api_key=settings.gemini_api_key)
_model = GoogleModel("gemini-2.5-flash", provider=_provider)

_audit_agent = Agent(
    _model,
    output_type=LGPDAuditReport,
    system_prompt=(
        "You are a Brazilian data protection expert specializing in LGPD "
        "(Lei Geral de Proteção de Dados, Law 13.709/2018). "
        "Analyze datasets for compliance violations and provide specific, "
        "actionable recommendations. Be concise and technically precise."
    ),
)

_categorizer_agent = Agent(
    _model,
    output_type=DomainClassification,
    system_prompt=(
        "You are a data engineering expert. Classify datasets into their primary domain "
        "based on column names, data types, and statistical characteristics. "
        "Be decisive — always choose the single most appropriate domain."
    ),
)

_anon_advisor_agent = Agent(
    _model,
    output_type=AnonAdvisoryReport,
    system_prompt=(
        "You are a privacy engineering expert. Recommend specific anonymization techniques "
        "for each PII column in a dataset. "
        "Available techniques: H3 Geohashing resolution 7 (coordinates), "
        "IP last-octet zeroing (IP addresses), SHA-256 + salt hashing (MACs and identifiers), "
        "date generalization to month/year (timestamps), "
        "k-anonymity aggregation (quasi-identifiers). "
        "Order priority_columns from highest to lowest re-identification risk."
    ),
)


def analyze_dataset(
    profile: DatasetProfile,
    scan: PIIScanResult,
    risk_score: int,
) -> CatalogAnalysis:
    """Runs the full agent crew analysis on a dataset profile.

    Executes three agents sequentially: LGPD auditor, domain classifier,
    and anonymization advisor. Results are aggregated into a single
    ``CatalogAnalysis`` object.

    Args:
        profile: Statistical profile from ``extract_profile``.
        scan: PII detection result from ``scan_pii``.
        risk_score: Privacy risk score from ``calculate_risk_score``.

    Returns:
        A ``CatalogAnalysis`` with audit, domain, and anonymization reports.
    """
    context = _build_context(profile, scan, risk_score)

    console.print("[blue]→ Running LGPD audit...[/blue]")
    audit = _audit_agent.run_sync(f"Audit this dataset for LGPD compliance:\n\n{context}")

    console.print("[blue]→ Classifying domain...[/blue]")
    domain = _categorizer_agent.run_sync(f"Classify the domain of this dataset:\n\n{context}")

    console.print("[blue]→ Advising anonymization strategy...[/blue]")
    anon = _anon_advisor_agent.run_sync(
        f"Recommend anonymization techniques for the PII fields in this dataset:\n\n{context}"
    )

    console.print("[green]✔ Analysis complete.[/green]")

    return CatalogAnalysis(
        dataset_slug=profile.dataset_slug,
        risk_score=risk_score,
        audit=audit.output,
        domain=domain.output,
        anonymization=anon.output,
    )


def _build_context(profile: DatasetProfile, scan: PIIScanResult, risk_score: int) -> str:
    pii_lines = "\n".join(
        f"  - {f.column_name}: {f.pii_type} | {f.lgpd_classification}" for f in scan.detected_fields
    )
    column_lines = "\n".join(
        f"  - {c.name} ({c.dtype}): {c.unique_count} unique values, "
        f"range [{c.min_value}, {c.max_value}]"
        if c.min_value is not None
        else f"  - {c.name} ({c.dtype}): {c.unique_count} unique values"
        for c in profile.columns
    )

    return (
        f"Dataset: {profile.dataset_slug}\n"
        f"Total files: {profile.total_files:,}\n"
        f"Sampled rows: {profile.total_rows:,}\n"
        f"Privacy Risk Score: {risk_score}/100\n"
        f"\nPII Fields Detected:\n{pii_lines}\n"
        f"\nAll Columns:\n{column_lines}"
    )
