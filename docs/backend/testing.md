# 后端测试

## 测试中间件

- 后端 pytest 通过 `backend/pyproject.toml` 的 `[tool.pytest_env]` 注入测试环境变量。
- 测试进程使用 `DATABASE_SCHEMA=fba_test`，后端启动、JWT 中间件、路由和后台任务都连接同一个测试数据库。
- 测试进程使用独立 Redis DB 和 `fba:test:*` 前缀；`backend/tests/conftest.py` 在测试会话开始和结束时清空测试 Redis DB。
- 测试进程使用独立 Celery Redis DB 和 `fba:test:celery` 前缀。
- `backend/tests/conftest.py` 在测试会话中启动真实 Celery worker 和 Celery beat，进程继承 pytest 注入的测试环境变量。
- Celery beat 在测试环境使用 `CELERY_TEST_BEAT_SCHEDULE=true` 切换到短周期测试调度。
- Celery 子进程由 pytest 进程通过 `subprocess` 启动，覆盖率通过 `backend/pyproject.toml` 的 coverage subprocess 配置合并。
- 对象存储测试使用 `OBJECT_STORAGE_DEFAULT_PREFIX=api-tests`。
- `backend/tests/conftest.py` 在测试会话开始时重建测试数据库并执行 Alembic 迁移，在测试会话结束时删除测试数据库。

## API 测试

- 黑盒 API 测试统一放在 `backend/tests/api/`。
- 测试通过 `TestClient` 调用公开 API，不直接调用 service、DAO、model 或内部依赖。
- 测试不使用 monkeypatch、mock、patch 或类似内部替身；需要覆盖分支时通过公开 HTTP 行为构造真实状态。
- 除 `backend/tests/conftest.py` 外，测试文件不直接导入后端内部包；需要复用的后端配置由 `DataStore` fixture 提供。
- 测试文件按路由结构组织：一个 router 文件对应一个测试文件，例如 `backend/app/admin/api/v1/sys/user.py` 对应 `backend/tests/api/admin/sys/test_user.py`。
- RBAC/权限测试数据入口是 `backend/tests/fixtures/rbac/`，测试侧 HTTP 创建与清理入口是 `backend/tests/api/rbac_helpers.py`。
- RBAC/权限测试清理顺序固定为用户、角色、数据范围、数据规则、部门、菜单。
