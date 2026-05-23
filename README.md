# KeelFrame

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](backend/pyproject.toml)
[![Node.js](https://img.shields.io/badge/Node.js-24-339933?logo=nodedotjs&logoColor=white)](.github/workflows/frontend-lint.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.123%2B-009688?logo=fastapi&logoColor=white)](backend/pyproject.toml)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](frontend/package.json)
[![Vite](https://img.shields.io/badge/Vite-Plus-646CFF?logo=vite&logoColor=white)](frontend/package.json)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)](frontend/package.json)
[![pytest](https://img.shields.io/badge/pytest-HTTP_black--box-0A9EDC?logo=pytest&logoColor=white)](backend/tests)
[![Coverage](https://img.shields.io/badge/Coverage-85%25+-31C654?logo=codecov&logoColor=white)](backend/.pre-commit-config.yaml)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](frontend/package.json)

KeelFrame 是面向 AI Native 开发的全栈工程底座，用来启动并持续演进后台类业务系统。

AI 能显著提高开发速度，但可靠交付依赖坚实起点：清晰边界、干净上下文、完整测试和质量门禁。KeelFrame 把这些约束放进同一个仓库，让 Agent 更容易理解系统，并用测试和构建反馈持续定位、修复问题。

仓库已包含前端管理台、后端 API、RBAC 权限模型、任务调度、本地联调脚本、测试入口和构建入口。业务开发可以直接扩展页面、领域模型和接口，并让新增代码进入测试、构建和 CI/CD 验证闭环。

## 项目定位

- 给 Agent 一个稳定上下文：目录边界、开发入口、测试入口和质量门禁集中在仓库内，减少协作时的上下文漂移。
- 让修改能被机器验证：后端黑盒 HTTP 测试、前端单元测试、构建脚本和 CI/CD 共同证明代码可用。
- 保留后台业务通用底座：用户、角色、菜单、部门、数据范围、数据规则、任务调度和系统管理能力可以直接扩展。
- 支持本地完整联调：根目录 `./dev.sh` 统一拉起前端、后端 API、Celery worker、Celery beat 和 Celery flower。

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
│   └── Dockerfile        # 后端服务与 Celery 镜像构建入口
├── frontend/             # Vue 3 管理后台
│   └── Dockerfile        # 前端镜像构建入口
├── deploy/               # 容器运行、进程管理与可观测性配置
├── docs/                 # 当前开发流程与约束文档
├── dev.sh                # 本地全栈开发启动脚本
└── docker-compose.yml    # 容器化依赖与服务编排
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
- 自动构建：前端构建入口是 `cd frontend && pnpm run build`，后端镜像入口是 `backend/Dockerfile`，前端镜像入口是 `frontend/Dockerfile`。
- 自动质量门禁：后端入口是 `cd backend && bash pre-commit.sh`，包含格式化、lint、类型检查、pytest 和覆盖率门禁；前端入口以 `frontend/package.json` 中的 `check`、`test`、`build` 脚本为准。
- CI/CD 验证：`.github/workflows/` 提供前后端自动检查入口；面向真实交付时，测试、构建和部署验证都应进入流水线，让最终结果由 CI/CD 状态证明。

新增模板能力时，需要同步补齐后端黑盒 HTTP 测试和前端单元测试，避免模板只可演示但不可长期维护。

## 开发入口

- 后端文档索引：`docs/backend/README.md`
- 后端启动约束：`docs/backend/dev-startup.md`
- 后端源码入口：`backend/backend/app/`
- 部署配置入口：`deploy/`
- 前端页面入口：`frontend/src/pages/`
- 前端 API 入口：`frontend/src/services/api/`

## 致谢

本项目基于以下开源项目继续整理和扩展：

- 后端基础来自 `fastapi-practices/fastapi_best_architecture`
- 前端基础来自 `Whbbit1999/shadcn-vue-admin`
