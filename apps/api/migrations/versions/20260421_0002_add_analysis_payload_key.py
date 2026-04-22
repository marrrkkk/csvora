"""add analysis payload key to import_results

Revision ID: 20260421_0002
Revises: 20260421_0001
Create Date: 2026-04-21 00:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260421_0002"
down_revision: Union[str, None] = "20260421_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("import_results", sa.Column("analysis_payload_key", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("import_results", "analysis_payload_key")
