"""System API v1 package."""

from fastapi import APIRouter

from backend.app.admin.api.v1.sys.dept import router as dept_router
from backend.app.admin.api.v1.sys.file import router as file_router
from backend.app.admin.api.v1.sys.menu import router as menu_router
from backend.app.admin.api.v1.sys.role import router as role_router
from backend.app.admin.api.v1.sys.user import router as user_router
from backend.app.config.api.v1.sys.config import router as config_router
from backend.app.notice.api.v1.sys.notice import router as notice_router
from backend.app.dict.api.v1.sys.dict_data import router as dict_data_router
from backend.app.dict.api.v1.sys.dict_type import router as dict_type_router
from backend.app.admin.api.v1.sys.data_rule import router as data_rule_router
from backend.app.admin.api.v1.sys.data_scope import router as data_scope_router


router: APIRouter = APIRouter(prefix="/sys")

router.include_router(dept_router, prefix="/depts", tags=["系统部门"])
router.include_router(menu_router, prefix="/menus", tags=["系统菜单"])
router.include_router(role_router, prefix="/roles", tags=["系统角色"])
router.include_router(user_router, prefix="/users", tags=["系统用户"])
router.include_router(data_rule_router, prefix="/data-rules", tags=["系统数据规则"])
router.include_router(data_scope_router, prefix="/data-scopes", tags=["系统数据范围"])
router.include_router(file_router, prefix="/files", tags=["系统文件"])
router.include_router(config_router, prefix="/configs", tags=["系统参数配置"])
router.include_router(dict_data_router, prefix="/dict-datas", tags=["系统字典数据"])
router.include_router(dict_type_router, prefix="/dict-types", tags=["系统字典类型"])
router.include_router(notice_router, prefix="/notices", tags=["系统通知公告"])
