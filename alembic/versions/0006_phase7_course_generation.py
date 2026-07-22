"""phase 7 cited course generation
Revision ID: 0006_phase7
Revises: 0005_phase6
"""

import sqlalchemy as sa

from alembic import op

revision = "0006_phase7"
down_revision = "0005_phase6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_generation_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id")),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_course_generation_idempotency"),
    )
    for table, parent in [
        ("curriculum_plans", "course_generation_jobs"),
        ("modules", "course_versions"),
        ("lessons", "modules"),
        ("learning_objectives", "lessons"),
        ("content_blocks", "lessons"),
        ("citations", "course_versions"),
        ("course_version_diffs", "courses"),
        ("generation_artifacts", "course_generation_jobs"),
    ]:
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("parent_id", sa.Uuid(), sa.ForeignKey(f"{parent}.id"), nullable=False),
            sa.Column("position", sa.Integer()),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(f"ix_{table}_parent", table, ["parent_id"])
    op.create_unique_constraint("uq_module_version_position", "modules", ["parent_id", "position"])
    op.create_unique_constraint("uq_lesson_module_position", "lessons", ["parent_id", "position"])
    op.create_unique_constraint(
        "uq_block_lesson_position", "content_blocks", ["parent_id", "position"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_block_lesson_position", "content_blocks")
    op.drop_constraint("uq_lesson_module_position", "lessons")
    op.drop_constraint("uq_module_version_position", "modules")
    for table in (
        "generation_artifacts",
        "course_version_diffs",
        "citations",
        "content_blocks",
        "learning_objectives",
        "lessons",
        "modules",
        "curriculum_plans",
    ):
        op.drop_index(f"ix_{table}_parent", table_name=table)
        op.drop_table(table)
    op.drop_table("course_generation_jobs")
