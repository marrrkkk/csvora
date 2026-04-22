"""init import tables

Revision ID: 20260421_0001
Revises:
Create Date: 2026-04-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260421_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import_status = sa.Enum(
        "created",
        "uploaded",
        "analyzing",
        "analyzed",
        "transforming",
        "completed",
        "failed",
        name="import_status",
    )
    import_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "imports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM(name="import_status", create_type=False), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=True),
        sa.Column("source_file_key", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)

    op.create_table(
        "import_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("field_name", sa.String(length=255), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_errors_import_id"), "import_errors", ["import_id"], unique=False)

    op.create_table(
        "import_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_column", sa.String(length=255), nullable=False),
        sa.Column("target_field", sa.String(length=255), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_mappings_import_id"), "import_mappings", ["import_id"], unique=False)

    op.create_table(
        "import_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("valid_row_count", sa.Integer(), nullable=False),
        sa.Column("invalid_row_count", sa.Integer(), nullable=False),
        sa.Column("cleaned_csv_key", sa.String(length=1024), nullable=True),
        sa.Column("normalized_json_key", sa.String(length=1024), nullable=True),
        sa.Column("validation_report_key", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_results_import_id"), "import_results", ["import_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_import_results_import_id"), table_name="import_results")
    op.drop_table("import_results")
    op.drop_index(op.f("ix_import_mappings_import_id"), table_name="import_mappings")
    op.drop_table("import_mappings")
    op.drop_index(op.f("ix_import_errors_import_id"), table_name="import_errors")
    op.drop_table("import_errors")
    op.drop_index(op.f("ix_api_keys_key_hash"), table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_table("imports")
    sa.Enum(name="import_status").drop(op.get_bind(), checkfirst=True)
