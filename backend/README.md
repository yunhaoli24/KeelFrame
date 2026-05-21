# Backend

这是 RBAC 全栈模板的后端服务，负责认证鉴权、权限模型、管理后台 API、任务调度、对象存储、OAuth2、邮件和后端基础设施。

## 当前定位

- 提供用户、角色、菜单、部门、数据范围、数据规则等 RBAC 基础模型。
- 提供登录、JWT 鉴权、中间件鉴权和管理后台 API。
- 提供 Celery worker、beat、flower 与调度任务入口。
- 提供数据库迁移、缓存、限流、日志、OpenTelemetry 和 Prometheus 相关基础能力。
- 作为后续业务模块的后端壳子，业务代码应沿用当前 `api`、`schema`、`service`、`crud`、`model` 分层组织。

## 目录入口

```text
backend/
├── backend/app/admin/     # 管理后台与 RBAC 核心模块
├── backend/app/task/      # Celery 任务入口
├── backend/app/config/    # 系统配置业务模块
├── backend/app/dict/      # 字典业务模块
├── backend/app/notice/    # 通知公告业务模块
├── backend/app/oauth2/    # OAuth2 业务模块
├── backend/app/s3/        # 对象存储业务模块
├── backend/app/email/     # 邮件业务模块
├── backend/common/        # 通用响应、异常、安全、分页等能力
├── backend/core/          # 配置与应用核心入口
├── backend/database/      # 数据库连接与会话
└── backend/alembic/       # 数据库迁移
```

## 开发入口

- 全栈启动：在仓库根目录运行 `./dev.sh`
- 后端质量检查：在 `backend/` 目录运行 `bash pre-commit.sh`
- 后端测试：以 `backend/tests/` 下的 pytest 用例为入口
- 后端文档索引：`../docs/backend/README.md`

## 约束

- 后端能力以当前代码路径为准，文档只维护入口、流程和约束。
- 新增管理后台能力时，同步补齐 schema、service、crud、model、API 和测试。
- 新增或调整本地启动流程时，同步更新 `../docs/backend/dev-startup.md`。
