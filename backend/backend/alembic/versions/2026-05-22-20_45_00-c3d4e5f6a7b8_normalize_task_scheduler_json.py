# ruff: noqa: ANN201, D103, D400, D415, E501, I001, N999, Q000, RUF100
"""normalize_task_scheduler_json

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-22 20:45:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE task_scheduler
        SET args = (args #>> '{}')::jsonb
        WHERE args IS NOT NULL
          AND jsonb_typeof(args::jsonb) = 'string'
        """
    )
    op.execute(
        """
        UPDATE task_scheduler
        SET kwargs = (kwargs #>> '{}')::jsonb
        WHERE kwargs IS NOT NULL
          AND jsonb_typeof(kwargs::jsonb) = 'string'
        """
    )


def downgrade():
    pass
