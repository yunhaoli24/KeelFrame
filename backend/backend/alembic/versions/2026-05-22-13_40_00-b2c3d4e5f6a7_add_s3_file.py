# ruff: noqa: ANN201, D103, D400, D415, E501, I001, N999, Q000, RUF001, RUF100
"""add_s3_file

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-22 13:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
import backend.common.model


# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "s3_file",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键 ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户 ID"),
        sa.Column("filename", sa.String(length=512), nullable=False, comment="对象文件名"),
        sa.Column("original_filename", sa.String(length=512), nullable=False, comment="原始文件名"),
        sa.Column("content_type", sa.String(length=255), nullable=True, comment="内容类型"),
        sa.Column("size", sa.BigInteger(), nullable=False, comment="文件大小"),
        sa.Column("bucket", sa.String(length=64), nullable=False, comment="存储桶"),
        sa.Column("prefix", sa.String(length=256), nullable=True, comment="前缀"),
        sa.Column("remark", backend.common.model.UniversalText(), nullable=True, comment="备注"),
        sa.Column("created_time", backend.common.model.TimeZone(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_time", backend.common.model.TimeZone(timezone=True), nullable=True, comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        comment="S3 文件.",
    )
    op.create_index(op.f("ix_s3_file_id"), "s3_file", ["id"], unique=True)
    op.create_index(op.f("ix_s3_file_user_id"), "s3_file", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_s3_file_user_id"), table_name="s3_file")
    op.drop_index(op.f("ix_s3_file_id"), table_name="s3_file")
    op.drop_table("s3_file")
