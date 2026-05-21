# ruff: noqa: ANN201, D103, D400, D415, E501, I001, N999, Q000, RUF001, RUF100, W291
"""add_celery_result_sequences

Revision ID: 399e142239d9
Revises: 7c767a61d67e
Create Date: 2026-05-21 19:48:40.761802

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '399e142239d9'
down_revision = '7c767a61d67e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.schema.CreateSequence(sa.Sequence("task_id_sequence")))
    op.execute(sa.schema.CreateSequence(sa.Sequence("taskset_id_sequence")))


def downgrade():
    op.execute(sa.schema.DropSequence(sa.Sequence("taskset_id_sequence")))
    op.execute(sa.schema.DropSequence(sa.Sequence("task_id_sequence")))
