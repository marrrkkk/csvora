"""ensure one import_result row per import

Revision ID: 20260422_0004
Revises: 20260422_0003
Create Date: 2026-04-22 00:50:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260422_0004"
down_revision: Union[str, None] = "20260422_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM import_results
        WHERE ctid IN (
            SELECT ctid
            FROM (
                SELECT
                    ctid,
                    ROW_NUMBER() OVER (
                        PARTITION BY import_id
                        ORDER BY created_at DESC, id DESC
                    ) AS row_num
                FROM import_results
            ) ranked
            WHERE ranked.row_num > 1
        )
        """
    )
    op.create_unique_constraint("uq_import_results_import_id", "import_results", ["import_id"])


def downgrade() -> None:
    op.drop_constraint("uq_import_results_import_id", "import_results", type_="unique")

