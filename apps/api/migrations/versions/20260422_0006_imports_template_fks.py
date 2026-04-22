"""imports template foreign keys

Revision ID: 20260422_0006
Revises: 20260422_0005
Create Date: 2026-04-22 12:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260422_0006"
down_revision: Union[str, None] = "20260422_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("imports", sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("imports", sa.Column("template_version_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_imports_template_id"), "imports", ["template_id"], unique=False)
    op.create_index(op.f("ix_imports_template_version_id"), "imports", ["template_version_id"], unique=False)
    op.create_foreign_key(
        "fk_imports_template_id",
        "imports",
        "templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_imports_template_version_id",
        "imports",
        "template_versions",
        ["template_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_imports_template_version_id", "imports", type_="foreignkey")
    op.drop_constraint("fk_imports_template_id", "imports", type_="foreignkey")
    op.drop_index(op.f("ix_imports_template_version_id"), table_name="imports")
    op.drop_index(op.f("ix_imports_template_id"), table_name="imports")
    op.drop_column("imports", "template_version_id")
    op.drop_column("imports", "template_id")
