"""Object storage schemas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectStorageConfig:
    """Resolved object storage configuration."""

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    prefix: str
    region: str


@dataclass(frozen=True)
class ObjectUploadResult:
    """Uploaded object metadata."""

    filename: str
    size: int
