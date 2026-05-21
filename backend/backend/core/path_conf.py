"""Path Conf."""

from pathlib import Path


# 项目根目录
BASE_PATH = Path(__file__).resolve().parent.parent

# alembic 迁移文件存放路径
ALEMBIC_DIR = BASE_PATH / "alembic"
ALEMBIC_INI = BASE_PATH / "alembic.ini"
ALEMBIC_VERSION_DIR = ALEMBIC_DIR / "versions"

# 日志文件路径
LOG_DIR = BASE_PATH / "log"

# 静态资源目录
STATIC_DIR = BASE_PATH / "static"

# 上传文件目录
UPLOAD_DIR = STATIC_DIR / "upload"
