"""phase 4 search, fetch, provenance, duplicate and quality metadata
Revision ID: 0003_phase4
Revises: 0002_phase3
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_phase4"
down_revision = "0002_phase3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_queries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("query_family", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(100)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_search_queries_project", "search_queries", ["project_id"])
    op.create_table(
        "search_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("query_id", sa.Uuid(), sa.ForeignKey("search_queries.id"), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("provider_rank", sa.Integer(), nullable=False),
        sa.Column("normalized_rank", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "query_id", "provider", "provider_rank", name="uq_search_result_provider_rank"
        ),
    )
    op.create_index("ix_search_results_canonical", "search_results", ["canonical_url"])
    op.create_table(
        "fetch_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("requested_url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("trace_id", sa.String(100), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_fetch_job_idempotency"),
    )
    op.create_table(
        "source_result_provenance",
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id"), primary_key=True),
        sa.Column(
            "search_result_id", sa.Uuid(), sa.ForeignKey("search_results.id"), primary_key=True
        ),
    )


def downgrade() -> None:
    op.drop_table("source_result_provenance")
    op.drop_table("fetch_jobs")
    op.drop_index("ix_search_results_canonical", table_name="search_results")
    op.drop_table("search_results")
    op.drop_index("ix_search_queries_project", table_name="search_queries")
    op.drop_table("search_queries")
