"""S3 file schemas."""

from datetime import datetime

from pydantic import Field, ConfigDict

from backend.common.schema import SchemaBase


class CreateS3FileParam(SchemaBase):
    """创建 S3 文件参数."""

    user_id: int = Field(description="用户 ID")
    filename: str = Field(description="对象文件名")
    original_filename: str = Field("", description="原始文件名")
    content_type: str | None = Field(None, description="内容类型")
    size: int = Field(0, description="文件大小")
    bucket: str = Field(description="存储桶")
    prefix: str | None = Field(None, description="前缀")
    remark: str | None = Field(None, description="备注")


class GetS3FileDetail(CreateS3FileParam):
    """S3 文件详情."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="S3 文件 ID")
    url: str = Field("", description="后端文件访问路径")
    created_time: datetime = Field(description="创建时间")
    updated_time: datetime | None = Field(None, description="更新时间")
