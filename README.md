# Full Stack RBAC Template

这是一个面向 AI Native 时代开发的 RBAC 全栈模板项目。它的目标不是只提供一套能跑起来的后台管理演示，而是提供一个干净、完整、可验证的项目骨架：AI 生成的每一行代码，都必须被自动测试、自动构建和自动部署验证，最终用 CI/CD 结果证明它能用。

AI 可以把开发速度提升几个数量级，但这种提升只有在好起点上才可靠。一个充满最佳实践、边界清晰、上下文不被污染的仓库，可以让 Agent 更容易理解系统；完整的测试和质量门禁，则能让 Agent 自动发现问题、定位问题并继续修复问题。

项目采用前后端分离结构：后端以 FastAPI 为核心，提供 RBAC 权限控制、管理后台 API、任务调度、插件化能力和可观测性基础；前端以 Vue 3、Vite、shadcn-vue 和 Tailwind CSS 为核心，提供后台管理界面、路由守卫、系统管理页面和统一 API 调用入口。后续业务开发可以在这个基础上直接扩展领域模型、业务页面和接口测试。

## 项目定位

- AI Native 开发骨架：为 AI Agent 提供清晰的项目边界、稳定的目录入口和可持续验证的工程流程。
- CI/CD 结果证明可用：代码合并前必须经过自动化质量门禁，交付结果以流水线验证结果为准。
- 测试驱动的 AI 协作：前后端都保留完整测试入口，让 Agent 可以通过测试失败自动发现并修复问题。
- RBAC 模板：内置用户、角色、菜单、部门、数据范围、数据规则等后台权限模型。
- 全栈脚手架：前端管理台、后端 API、数据库、缓存、任务队列和后台任务入口放在同一个仓库内维护。
- 开发壳子：保留通用后台能力，业务项目只需要在此基础上新增业务模块。
- 测试优先：后端以 pytest 覆盖 API 边界，前端以 Vitest 覆盖路由、状态和 API 调用等核心行为。
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

这个仓库把“AI 写得快”约束在“机器能证明可用”的闭环里：

- 自动测试：后端测试位于 `backend/tests/`，以 pytest 和 `TestClient` 通过公开 HTTP API 做黑盒验证；测试不通过 service、DAO、model 或内部 mock 绕过真实行为。更多约束见 `docs/backend/testing.md`。
- 前端测试：前端测试位于 `frontend/src/**/*.test.ts`，以 `pnpm run test` 验证路由守卫、状态管理、API 调用和通用工具等核心行为。
- 自动构建：前端构建入口是 `cd frontend && pnpm run build`，全栈镜像入口是根目录 `Dockerfile`。
- 自动质量门禁：后端入口是 `cd backend && bash pre-commit.sh`，包含格式化、lint、类型检查、pytest 和覆盖率门禁；前端入口以 `frontend/package.json` 中的 `check`、`test`、`build` 脚本为准。
- CI/CD 验证：`.github/workflows/` 提供前后端自动检查入口；面向真实交付时，测试、构建和部署验证都应进入流水线，让最终结果由 CI/CD 状态证明。

新增模板能力时，需要同步补齐后端黑盒 HTTP 测试和前端单元测试，避免模板只可演示但不可长期维护。

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
