"""import_status new values and import_mapping_suggestions

Revision ID: 20260422_0007
Revises: 20260422_0006
Create Date: 2026-04-22 12:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260422_0007"
down_revision: Union[str, None] = "20260422_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'import_status' AND e.enumlabel = 'needs_review'
    ) THEN
        ALTER TYPE import_status ADD VALUE 'needs_review';
    END IF;
END $$;
"""
        )
    )
    op.execute(
        sa.text(
            """
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'import_status' AND e.enumlabel = 'ready_to_transform'
    ) THEN
        ALTER TYPE import_status ADD VALUE 'ready_to_transform';
    END IF;
END $$;
"""
        )
    )

    op.create_table(
        "import_mapping_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_column", sa.String(length=255), nullable=False),
        sa.Column("target_field", sa.String(length=255), nullable=True),
        sa.Column("confidence_score", sa.Numeric(precision=6, scale=5), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("auto_accepted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_import_mapping_suggestions_import_id"),
        "import_mapping_suggestions",
        ["import_id"],
        unique=False,
    )

    op.add_column("import_results", sa.Column("template_version_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "import_results",
        sa.Column("analysis_used_ai", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_foreign_key(
        "fk_import_results_template_version_id",
        "import_results",
        "template_versions",
        ["template_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_import_results_template_version_id", "import_results", type_="foreignkey")
    op.drop_column("import_results", "analysis_used_ai")
    op.drop_column("import_results", "template_version_id")
    op.drop_index(op.f("ix_import_mapping_suggestions_import_id"), table_name="import_mapping_suggestions")
    op.drop_table("import_mapping_suggestions")
    # Cannot remove enum values safely in PostgreSQL; leave import_status labels in place.
