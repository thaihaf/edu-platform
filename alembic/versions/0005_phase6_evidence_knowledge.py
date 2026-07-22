"""phase 6 evidence and knowledge foundations
Revision ID: 0005_phase6
Revises: 0004_phase5
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_phase6"
down_revision = "0004_phase5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "claims",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("normalized_statement", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(64), nullable=False),
        sa.Column("subject_entities", sa.JSON(), nullable=False),
        sa.Column("temporal_scope", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supersedes_claim_id", sa.Uuid(), sa.ForeignKey("claims.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("project_id", "fingerprint", name="uq_claim_project_fingerprint"),
    )
    op.create_index("ix_claims_project_status", "claims", ["project_id", "status"])
    for name in (
        "evidence_links",
        "source_independence_clusters",
        "claim_confidence_assessments",
        "reported_questions",
        "skills",
        "skill_prerequisites",
        "knowledge_gaps",
        "review_decisions",
    ):
        op.create_table(
            name,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False
            ),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(f"ix_{name}_project", name, ["project_id"])


def downgrade() -> None:
    for name in (
        "review_decisions",
        "knowledge_gaps",
        "skill_prerequisites",
        "skills",
        "reported_questions",
        "claim_confidence_assessments",
        "source_independence_clusters",
        "evidence_links",
    ):
        op.drop_index(f"ix_{name}_project", table_name=name)
        op.drop_table(name)
    op.drop_index("ix_claims_project_status", table_name="claims")
    op.drop_table("claims")
