"""create phase 2 domain data tables

Revision ID: 0001_domain_data
Revises:
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_domain_data"
down_revision = None
branch_labels = None
depends_on = None
uuid = postgresql.UUID(as_uuid=True)
json = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "research_projects",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("workspace_id", uuid, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("locale", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("research_depth", sa.Integer(), nullable=False),
        sa.Column("created_by", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "sources",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("project_id", uuid, sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("canonical_url", sa.Text()),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "source_snapshots",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("source_id", uuid, sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", json, nullable=False),
        sa.UniqueConstraint("source_id", "content_hash", name="uq_source_snapshot_hash"),
    )
    op.create_table(
        "courses",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("project_id", uuid, sa.ForeignKey("research_projects.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "course_versions",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("course_id", uuid, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("content_json", json, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("course_id", "version_number", name="uq_course_version_number"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", uuid, nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor_id", uuid),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details_json", json, nullable=False),
    )


def downgrade() -> None:
    for table in (
        "audit_events",
        "course_versions",
        "courses",
        "source_snapshots",
        "sources",
        "research_projects",
    ):
        op.drop_table(table)
