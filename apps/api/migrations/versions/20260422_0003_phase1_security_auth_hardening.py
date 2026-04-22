"""phase 1 security and auth hardening

Revision ID: 20260422_0003
Revises: 20260421_0002
Create Date: 2026-04-22 00:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260422_0003"
down_revision: Union[str, None] = "20260421_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("key_prefix", sa.String(length=16), nullable=True))
    op.add_column("api_keys", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("api_keys", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("api_keys", sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_api_keys_key_prefix"), "api_keys", ["key_prefix"], unique=False)

    op.add_column("imports", sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_imports_api_key_id"), "imports", ["api_key_id"], unique=False)
    op.create_foreign_key(
        "fk_imports_api_key_id",
        source_table="imports",
        referent_table="api_keys",
        local_cols=["api_key_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_imports_api_key_id", "imports", type_="foreignkey")
    op.drop_index(op.f("ix_imports_api_key_id"), table_name="imports")
    op.drop_column("imports", "api_key_id")

    op.drop_index(op.f("ix_api_keys_key_prefix"), table_name="api_keys")
    op.drop_column("api_keys", "last_used_at")
    op.drop_column("api_keys", "expires_at")
    op.drop_column("api_keys", "revoked_at")
    op.drop_column("api_keys", "key_prefix")

