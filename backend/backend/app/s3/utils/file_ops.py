"""File Ops."""

from urllib.parse import quote

import httpx
from fastapi import UploadFile
from opendal import AsyncOperator
from fastapi.responses import Response

from backend.app.s3.model import S3Storage
from backend.utils.file_ops import build_filename
from backend.common.exception import errors


S3_PROXY_HEADERS = {
    "accept-ranges",
    "cache-control",
    "content-disposition",
    "content-length",
    "content-type",
    "etag",
    "expires",
    "last-modified",
}


def _quote_s3_path(value: str) -> str:
    """Quote S3 path segments while preserving path separators."""
    return "/".join(quote(part, safe="") for part in value.strip("/").split("/") if part)


def build_s3_object_url(endpoint: str, bucket: str, prefix: str | None, filename: str) -> str:
    """Build the internal upstream URL used by backend S3 proxy endpoints."""
    key = "/".join(part for part in (prefix.strip("/") if prefix else "", filename.lstrip("/")) if part)
    return f"{endpoint.rstrip('/')}/{_quote_s3_path(bucket)}/{_quote_s3_path(key)}"


async def proxy_s3_get(url: str) -> Response:
    """Forward a GET request to S3-compatible storage and return the upstream response."""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            upstream = await client.get(url)
    except httpx.HTTPError as e:
        raise errors.GatewayError(msg="对象存储访问失败") from e

    headers = {key: value for key, value in upstream.headers.items() if key.lower() in S3_PROXY_HEADERS}
    return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)


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
    filename = build_filename(file)

    op = get_operator(
        s3_storage.endpoint,
        s3_storage.access_key,
        s3_storage.secret_key,
        s3_storage.bucket,
        s3_storage.prefix or "/",
        s3_storage.region or "any",
    )
    contents = await file.read()
    if not contents:
        raise errors.RequestError(msg="上传文件不能为空")
    await op.write(filename, contents)
    await file.close()
    return filename


async def read_file(s3_storage: S3Storage, filename: str) -> bytes:
    """Read a file from S3-compatible storage."""
    op = get_operator(
        s3_storage.endpoint,
        s3_storage.access_key,
        s3_storage.secret_key,
        s3_storage.bucket,
        s3_storage.prefix or "/",
        s3_storage.region or "any",
    )
    return bytes(await op.read(filename))  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
