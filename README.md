# Full Stack RBAC Template

这是一个面向业务系统快速启动的 RBAC 全栈模板项目，目标是把后台管理系统中反复出现的认证、授权、用户体系、菜单权限、数据权限和基础运维能力沉淀成一个可复用的开发壳子。

项目采用前后端分离结构：后端以 FastAPI 为核心，提供 RBAC 权限控制、管理后台 API、任务调度、插件化能力和可观测性基础；前端以 Vue 3、Vite、shadcn-vue 和 Tailwind CSS 为核心，提供后台管理界面、路由守卫、系统管理页面和统一 API 调用入口。后续业务开发可以在这个基础上直接扩展领域模型、业务页面和接口测试。

## 项目定位

- RBAC 模板：内置用户、角色、菜单、部门、数据范围、数据规则等后台权限模型。
- 全栈脚手架：前端管理台、后端 API、数据库、缓存、任务队列和后台任务入口放在同一个仓库内维护。
- 开发壳子：保留通用后台能力，业务项目只需要在此基础上新增业务模块。
- 测试优先：后端以 pytest 覆盖 API 与服务边界，前端测试体系按页面、组件和用户流程补齐，作为模板交付标准持续完善。
- 本地联调友好：根目录 `./dev.sh` 统一拉起前端、后端 API、Celery worker、Celery beat 和 Celery flower。

## 已包含能力

- 认证授权：登录、JWT 鉴权、中间件鉴权、路由守卫。
- 权限管理：用户管理、角色管理、菜单管理、角色菜单绑定。
- 数据权限：数据范围、数据规则、角色数据权限配置入口。
- 系统基础：部门、登录日志、操作日志、在线用户、系统配置、字典、通知等后台常见模块。
- 任务能力：Celery worker、beat、flower 与调度任务管理入口。
- 前端基础设施：自动路由、布局、Pinia、TanStack Vue Query、Axios 封装、数据表格、主题切换。
- 后端基础设施：FastAPI、SQLAlchemy、Pydantic、Alembic、Redis、RabbitMQ、OpenTelemetry、Prometheus 相关配置。

## 目录结构

```text
.
├── backend/              # FastAPI 后端服务、RBAC 模型、API、任务与插件
├── frontend/             # Vue 3 管理后台
├── docs/                 # 当前开发流程与约束文档
├── dev.sh                # 本地全栈开发启动脚本
├── docker-compose.yml    # 容器化依赖与服务编排
└── Dockerfile            # 前后端镜像构建入口
```

## 本地开发

全栈开发统一使用根目录脚本启动：

```bash
./dev.sh
```

脚本会启动前端、后端 API、Celery worker、Celery beat 和 Celery flower，并处理后端 API 与 flower 的端口冲突。更多约束见 `docs/backend/dev-startup.md`。

## 测试与质量

- 后端测试入口位于 `backend/backend/app/admin/tests/`，当前以 pytest 为基础。
- 后端 lint 与类型检查约束见 `docs/backend/lint-pyright.md`。
- 前端质量入口以 `frontend/package.json` 中的 lint 脚本为准。
- 新增模板能力时，需要同步补齐后端 API/服务测试和前端页面/组件/流程测试，避免模板只可演示但不可长期维护。

## 开发入口

- 后端文档索引：`docs/backend/README.md`
- 后端启动约束：`docs/backend/dev-startup.md`
- 后端源码入口：`backend/backend/app/`
- 前端页面入口：`frontend/src/pages/`
- 前端 API 入口：`frontend/src/services/api/`

## 致谢

本项目基于以下开源项目继续整理和扩展：

- 后端基础来自 `fastapi-practices/fastapi_best_architecture`
- 前端基础来自 `Whbbit1999/shadcn-vue-admin`
