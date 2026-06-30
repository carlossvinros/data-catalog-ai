"""SQLAlchemy ORM models for the data catalog."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Computed,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from data_catalog.catalog.database import Base


class Dataset(Base):
    """Core catalog entry for a single ingested dataset."""

    __tablename__ = "datasets"
    __table_args__ = (Index("ix_datasets_search_vector", "search_vector", postgresql_using="gin"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    domain: Mapped[str | None] = mapped_column(String)
    total_files: Mapped[int | None] = mapped_column(Integer)
    total_rows: Mapped[int | None] = mapped_column(Integer)
    sampled_files: Mapped[int | None] = mapped_column(Integer)
    risk_score: Mapped[int | None] = mapped_column(Integer)
    is_compliant: Mapped[bool | None] = mapped_column(Boolean)
    audit_summary: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english',"
            " coalesce(slug, '') || ' ' ||"
            " coalesce(domain, '') || ' ' ||"
            " coalesce(description, ''))",
            persisted=True,
        ),
        nullable=True,
    )

    columns: Mapped[list["DatasetColumn"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )
    pii_detections: Mapped[list["PIIDetection"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )
    anon_recommendations: Mapped[list["AnonRecommendation"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )
    audit_runs: Mapped[list["AuditRun"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class DatasetColumn(Base):
    """Statistical profile of a single column within a dataset."""

    __tablename__ = "dataset_columns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dtype: Mapped[str | None] = mapped_column(String)
    null_pct: Mapped[float | None] = mapped_column(Float)
    unique_count: Mapped[int | None] = mapped_column(Integer)
    min_value: Mapped[float | None] = mapped_column(Float)
    max_value: Mapped[float | None] = mapped_column(Float)

    dataset: Mapped[Dataset] = relationship(back_populates="columns")


class PIIDetection(Base):
    """A personally identifiable field detected within a dataset."""

    __tablename__ = "pii_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    column_name: Mapped[str] = mapped_column(String, nullable=False)
    pii_type: Mapped[str] = mapped_column(String, nullable=False)
    lgpd_classification: Mapped[str] = mapped_column(String, nullable=False)

    dataset: Mapped[Dataset] = relationship(back_populates="pii_detections")


class AnonRecommendation(Base):
    """Anonymization technique recommended for a PII column."""

    __tablename__ = "anonymization_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    column_name: Mapped[str] = mapped_column(String, nullable=False)
    technique: Mapped[str] = mapped_column(String, nullable=False)
    justification: Mapped[str | None] = mapped_column(Text)

    dataset: Mapped[Dataset] = relationship(back_populates="anon_recommendations")


class AuditRun(Base):
    """Record of a single LGPD audit execution for a dataset."""

    __tablename__ = "audit_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True)
    audit_summary: Mapped[str | None] = mapped_column(Text)
    violations: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    recommendations: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dataset: Mapped[Dataset] = relationship(back_populates="audit_runs")
