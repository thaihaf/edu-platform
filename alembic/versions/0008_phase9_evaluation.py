"""Phase 9 evaluation and quality-gate platform.

Revision ID: 0008_phase9_evaluation
Revises: 0007_phase8
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_phase9_evaluation"
down_revision = "0007_phase8"
branch_labels = None
depends_on = None
TABLES = (
    "golden_datasets",
    "golden_dataset_versions",
    "evaluation_cases",
    "evaluation_runs",
    "evaluation_results",
    "evaluation_aggregates",
    "metric_definitions",
    "quality_gate_policies",
    "quality_gate_policy_versions",
    "quality_gate_decisions",
    "evaluation_baselines",
    "regression_comparisons",
)


def upgrade() -> None:
    op.create_table(
        "golden_datasets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("locale", sa.String(32), nullable=False),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "golden_dataset_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("dataset_id", sa.Uuid(), sa.ForeignKey("golden_datasets.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.UniqueConstraint("dataset_id", "version_number", name="uq_golden_dataset_version"),
    )
    op.create_table(
        "evaluation_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "dataset_version_id",
            sa.Uuid(),
            sa.ForeignKey("golden_dataset_versions.id"),
            nullable=False,
        ),
        sa.Column("case_key", sa.String(255), nullable=False),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("input_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint("dataset_version_id", "case_key", name="uq_evaluation_case_key"),
    )
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(), sa.ForeignKey("golden_dataset_versions.id")),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.UniqueConstraint("project_id", "idempotency_key", name="uq_evaluation_run_idempotency"),
    )
    for table in TABLES[4:]:
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "evaluation_run_id", sa.Uuid(), sa.ForeignKey("evaluation_runs.id"), nullable=True
            ),
            sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        )
    op.create_index(
        "ix_evaluation_runs_project_status", "evaluation_runs", ["project_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_evaluation_runs_project_status", table_name="evaluation_runs")
    for table in reversed(TABLES):
        op.drop_table(table)
