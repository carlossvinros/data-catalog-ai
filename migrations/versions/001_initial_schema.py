"""Initial catalog schema.

Revision ID: 001
Revises:
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String, nullable=False),
        sa.Column("domain", sa.String),
        sa.Column("total_files", sa.Integer),
        sa.Column("total_rows", sa.Integer),
        sa.Column("sampled_files", sa.Integer),
        sa.Column("risk_score", sa.Integer),
        sa.Column("is_compliant", sa.Boolean),
        sa.Column("audit_summary", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR,
            sa.Computed(
                "to_tsvector('english',"
                " coalesce(slug, '') || ' ' ||"
                " coalesce(domain, '') || ' ' ||"
                " coalesce(description, ''))",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index("ix_datasets_slug", "datasets", ["slug"], unique=True)
    op.create_index(
        "ix_datasets_search_vector",
        "datasets",
        ["search_vector"],
        postgresql_using="gin",
    )

    op.create_table(
        "dataset_columns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("dataset_id", sa.Integer, sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("dtype", sa.String),
        sa.Column("null_pct", sa.Float),
        sa.Column("unique_count", sa.Integer),
        sa.Column("min_value", sa.Float),
        sa.Column("max_value", sa.Float),
    )
    op.create_index("ix_dataset_columns_dataset_id", "dataset_columns", ["dataset_id"])

    op.create_table(
        "pii_detections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("dataset_id", sa.Integer, sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("column_name", sa.String, nullable=False),
        sa.Column("pii_type", sa.String, nullable=False),
        sa.Column("lgpd_classification", sa.String, nullable=False),
    )
    op.create_index("ix_pii_detections_dataset_id", "pii_detections", ["dataset_id"])

    op.create_table(
        "anonymization_recommendations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("dataset_id", sa.Integer, sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("column_name", sa.String, nullable=False),
        sa.Column("technique", sa.String, nullable=False),
        sa.Column("justification", sa.Text),
    )
    op.create_index(
        "ix_anon_recommendations_dataset_id",
        "anonymization_recommendations",
        ["dataset_id"],
    )

    op.create_table(
        "audit_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("dataset_id", sa.Integer, sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("audit_summary", sa.Text),
        sa.Column("violations", postgresql.ARRAY(sa.String)),
        sa.Column("recommendations", postgresql.ARRAY(sa.String)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_runs_dataset_id", "audit_runs", ["dataset_id"])


def downgrade() -> None:
    op.drop_table("audit_runs")
    op.drop_table("anonymization_recommendations")
    op.drop_table("pii_detections")
    op.drop_table("dataset_columns")
    op.drop_table("datasets")
