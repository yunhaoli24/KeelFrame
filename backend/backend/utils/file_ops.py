"""File Ops."""

from anyio import open_file
from fastapi import UploadFile

from backend.core.conf import settings
from backend.common.log import log
from backend.common.enums import FileType
from backend.core.path_conf import UPLOAD_DIR
from backend.utils.timezone import timezone
from backend.common.exception import errors


def _require_filename(file: UploadFile) -> str:
    """Validate upload filename and return a non-empty value."""
    filename = file.filename
    if not filename:
        raise errors.RequestError(msg="文件名不能为空")
    return filename


def build_filename(file: UploadFile) -> str:
    """构建文件名.

    :param file: FastAPI 上传文件对象
    :return:
    """
    timestamp = int(timezone.now().timestamp())
    filename = _require_filename(file)
    file_ext = filename.split(".")[-1].lower()
    return f"{filename.replace(f'.{file_ext}', f'_{timestamp}')}.{file_ext}"


def upload_file_verify(file: UploadFile) -> None:
    """文件验证.

    :param file: FastAPI 上传文件对象
    :return:
    """
    filename = _require_filename(file)
    file_ext = filename.split(".")[-1].lower()
    if not file_ext:
        raise errors.RequestError(msg="未知的文件类型")

    file_size = file.size
    if file_size is None:
        raise errors.RequestError(msg="无法识别文件大小")

    if file_ext == FileType.image:
        if file_ext not in settings.UPLOAD_IMAGE_EXT_INCLUDE:
            raise errors.RequestError(msg="此图片格式暂不支持")
        if file_size > settings.UPLOAD_IMAGE_SIZE_MAX:
            raise errors.RequestError(msg="图片超出最大限制, 请重新选择")
    elif file_ext == FileType.video:
        if file_ext not in settings.UPLOAD_VIDEO_EXT_INCLUDE:
            raise errors.RequestError(msg="此视频格式暂不支持")
        if file_size > settings.UPLOAD_VIDEO_SIZE_MAX:
            raise errors.RequestError(msg="视频超出最大限制, 请重新选择")


async def upload_file(file: UploadFile) -> str:
    """上传文件.

    :param file: FastAPI 上传文件对象
    :return:
    """
    filename = build_filename(file)
    try:
        async with await open_file(UPLOAD_DIR / filename, mode="wb") as fb:
            while True:
                content = await file.read(settings.UPLOAD_READ_SIZE)
                if not content:
                    break
                await fb.write(content)
    except Exception as e:
        log.error(f"上传文件 {filename} 失败: {e!s}")
        raise errors.RequestError(msg="上传文件失败") from e
    await file.close()
    return filename
