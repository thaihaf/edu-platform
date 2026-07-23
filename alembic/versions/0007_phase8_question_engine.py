"""phase 8 validated question engine
Revision ID: 0007_phase8
Revises: 0006_phase7
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_phase8"
down_revision = "0006_phase7"
branch_labels = None
depends_on = None


def _table(name: str, parent: str, unique: tuple[str, ...] | None = None) -> None:
    constraints = (
        [sa.UniqueConstraint(*unique, name=f"uq_{name}_{'_'.join(unique)}")] if unique else []
    )
    op.create_table(
        name,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey(f"{parent}.id"), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        *constraints,
    )
    op.create_index(f"ix_{name}_parent", name, ["parent_id"])


def upgrade() -> None:
    op.create_table(
        "question_generation_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id")),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "project_id", "idempotency_key", name="uq_question_generation_project_key"
        ),
    )
    op.create_table(
        "question_banks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    _table("question_bank_versions", "question_banks", ("parent_id", "id"))
    for name, parent in [
        ("question_blueprints", "question_generation_jobs"),
        ("questions", "question_bank_versions"),
        ("question_options", "questions"),
        ("question_citations", "questions"),
        ("question_validation_results", "questions"),
        ("question_review_decisions", "questions"),
        ("question_revisions", "questions"),
        ("question_duplicate_clusters", "research_projects"),
        ("question_duplicate_cluster_members", "question_duplicate_clusters"),
        ("question_bank_version_diffs", "question_banks"),
        ("question_generation_events", "question_generation_jobs"),
    ]:
        _table(name, parent)


def downgrade() -> None:
    for name in (
        "question_generation_events",
        "question_bank_version_diffs",
        "question_duplicate_cluster_members",
        "question_duplicate_clusters",
        "question_revisions",
        "question_review_decisions",
        "question_validation_results",
        "question_citations",
        "question_options",
        "questions",
        "question_blueprints",
        "question_bank_versions",
    ):
        op.drop_index(f"ix_{name}_parent", table_name=name)
        op.drop_table(name)
    op.drop_table("question_banks")
    op.drop_table("question_generation_jobs")
