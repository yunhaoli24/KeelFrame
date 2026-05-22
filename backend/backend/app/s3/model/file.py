"""S3 file."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class S3File(Base):
    """S3 文件."""

    __tablename__ = "s3_file"  # pyright: ignore[reportAssignmentType]

    id: Mapped[id_key] = mapped_column(init=False)
    user_id: Mapped[int] = mapped_column(sa.BigInteger, index=True, comment="用户 ID")
    filename: Mapped[str] = mapped_column(sa.String(512), comment="对象文件名")
    bucket: Mapped[str] = mapped_column(sa.String(64), comment="存储桶")
    original_filename: Mapped[str] = mapped_column(sa.String(512), default="", comment="原始文件名")
    content_type: Mapped[str | None] = mapped_column(sa.String(255), default=None, comment="内容类型")
    size: Mapped[int] = mapped_column(sa.BigInteger, default=0, comment="文件大小")
    prefix: Mapped[str | None] = mapped_column(sa.String(256), default=None, comment="前缀")
    remark: Mapped[str | None] = mapped_column(UniversalText, default=None, comment="备注")
