"""schema_type column, import mapping trace columns, template version validation_rules

Revision ID: 20260422_0008
Revises: 20260422_0007
Create Date: 2026-04-22 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260422_0008"
down_revision: Union[str, None] = "20260422_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "templates",
        "entity_type",
        new_column_name="schema_type",
        existing_type=sa.String(length=32),
        type_=sa.String(length=128),
        existing_nullable=False,
    )

    op.add_column("imports", sa.Column("mappings_finalized_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("imports", sa.Column("final_mapping_revision", sa.Integer(), server_default="0", nullable=False))
    op.add_column(
        "template_versions",
        sa.Column("validation_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "import_final_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_column", sa.String(length=255), nullable=False),
        sa.Column("target_field", sa.String(length=255), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=6, scale=5), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_version_id"], ["template_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("import_id", "revision", "source_column", name="uq_import_final_mappings_rev_source"),
    )
    op.create_index(op.f("ix_import_final_mappings_import_id"), "import_final_mappings", ["import_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_import_final_mappings_import_id"), table_name="import_final_mappings")
    op.drop_table("import_final_mappings")
    op.drop_column("template_versions", "validation_rules")
    op.drop_column("imports", "final_mapping_revision")
    op.drop_column("imports", "mappings_finalized_at")
    op.alter_column(
        "templates",
        "schema_type",
        new_column_name="entity_type",
        existing_type=sa.String(length=128),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
