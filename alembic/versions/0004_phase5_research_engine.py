"""phase 5 resumable research orchestration
Revision ID: 0004_phase5
Revises: 0003_phase4
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_phase5"
down_revision = "0003_phase4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("current_phase", sa.String(32), nullable=False),
        sa.Column("current_node", sa.String(100), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("budgets_json", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("workflow_version", sa.String(64), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("trace_id", sa.String(100), nullable=False),
        sa.Column("error_code", sa.String(100)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_research_job_idempotency"),
    )
    op.create_index("ix_research_jobs_project_status", "research_jobs", ["project_id", "status"])
    for table in (
        "research_checkpoints",
        "research_artifacts",
        "research_observations",
        "research_gaps",
        "research_events",
    ):
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "research_job_id", sa.Uuid(), sa.ForeignKey("research_jobs.id"), nullable=False
            ),
            sa.Column("kind", sa.String(100), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(f"ix_{table}_job", table, ["research_job_id"])


def downgrade() -> None:
    for table in (
        "research_events",
        "research_gaps",
        "research_observations",
        "research_artifacts",
        "research_checkpoints",
    ):
        op.drop_index(f"ix_{table}_job", table_name=table)
        op.drop_table(table)
    op.drop_index("ix_research_jobs_project_status", table_name="research_jobs")
    op.drop_table("research_jobs")
