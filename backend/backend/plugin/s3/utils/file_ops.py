"""File Ops."""

from fastapi import UploadFile
from opendal import AsyncOperator

from backend.plugin.s3.model import S3Storage
from backend.common.exception import errors


def get_operator(
    endpoint: str, access_key: str, secret_key: str, bucket: str, prefix: str, region: str
) -> AsyncOperator:
    """获取操作.

    :param endpoint: 终端节点
    :param access_key: 访问密钥
    :param secret_key: 密钥
    :param bucket: 存储桶
    :param prefix: 前缀
    :param region: 区域
    :return:
    """
    return AsyncOperator(
        "s3",
        endpoint=endpoint,
        access_key_id=access_key,
        secret_access_key=secret_key,
        bucket=bucket,
        root=prefix,
        region=region,
    )


async def write_file(s3_storage: S3Storage, file: UploadFile) -> str:
    """写入文件.

    :param s3_storage: S3 存储
    :param file: 上传文件
    :return:
    """
    filename = file.filename
    if not filename:
        raise errors.RequestError(msg="文件名不能为空")

    op = get_operator(
        s3_storage.endpoint,
        s3_storage.access_key,
        s3_storage.secret_key,
        s3_storage.bucket,
        s3_storage.prefix or "/",
        s3_storage.region or "any",
    )
    contents = await file.read()
    await op.write(filename, contents)
    return filename
