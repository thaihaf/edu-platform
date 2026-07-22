"""phase 3 ingestion jobs and chunks

Revision ID: 0002_phase3
Revises: 0001_phase2
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_phase3"
down_revision = "0001_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # JSON keeps metadata/text usable everywhere; pgvector index setup is integration-only.
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), sa.ForeignKey("source_snapshots.id")),
        sa.Column("input_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("stage", sa.String(16), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(100)),
        sa.Column("error_message", sa.Text()),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("trace_id", sa.String(100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_ingestion_job_idempotency"),
    )
    op.create_index("ix_ingestion_jobs_project", "ingestion_jobs", ["project_id"])
    op.create_table(
        "source_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_snapshot_id", sa.Uuid(), sa.ForeignKey("source_snapshots.id"), nullable=False
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer()),
        sa.Column("page_end", sa.Integer()),
        sa.Column("section_path", sa.JSON(), nullable=False),
        sa.Column("heading", sa.String(500)),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("chunk_hash", sa.String(64), nullable=False),
        sa.Column("embedding_json", sa.JSON()),
        sa.Column("embedding_model", sa.String(255)),
        sa.Column("embedding_dimension", sa.Integer()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_snapshot_id", "chunk_hash", name="uq_chunk_snapshot_hash"),
    )
    op.create_index("ix_source_chunks_snapshot", "source_chunks", ["source_snapshot_id"])


def downgrade() -> None:
    op.drop_table("source_chunks")
    op.drop_table("ingestion_jobs")
