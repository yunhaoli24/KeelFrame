"""Storage."""

from datetime import datetime

from pydantic import Field, ConfigDict

from backend.common.schema import SchemaBase


class S3StorageSchemaBase(SchemaBase):
    """S3 存储基础模型."""

    name: str = Field(description="存储名称")
    endpoint: str = Field(description="终端节点")
    access_key: str = Field(description="访问密钥")
    secret_key: str = Field(description="密钥")
    bucket: str = Field(description="存储桶")
    prefix: str | None = Field(None, description="前缀")
    region: str | None = Field(None, description="区域")
    remark: str | None = Field(None, description="备注")


class CreateS3StorageParam(S3StorageSchemaBase):
    """创建 S3 存储参数."""


class UpdateS3StorageParam(S3StorageSchemaBase):
    """更新 S3 存储参数."""


class DeleteS3StorageParam(SchemaBase):
    """删除 S3 存储参数."""

    pks: list[int] = Field(description="S3 存储 ID 列表")


class GetS3StorageDetail(S3StorageSchemaBase):
    """S3 存储详情."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="S3 存储 ID")
    created_time: datetime = Field(description="创建时间")
    updated_time: datetime | None = Field(None, description="更新时间")
