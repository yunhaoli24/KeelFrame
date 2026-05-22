# 后端 lint、pyright 与 ty 约束

## 结论

- 后端质量检查统一从 `backend/` 目录运行 `bash pre-commit.sh`。
- `backend/pre-commit.sh` 直接运行 `uv run prek run --all-files`。
- 后端测试作为 local pre-commit hook 配置在 `backend/.pre-commit-config.yaml`。
- GitHub backend CI 会启动 Postgres、Redis 和对象存储依赖，并在 lint 前执行数据库迁移。
- pre-commit 使用项目本地环境运行 `uv run ty check`。
- pre-commit hooks 统一使用 `repo: local` 和项目本地工具。

## 入口

- 运行命令：`cd backend && bash pre-commit.sh`
- pre-commit 入口：`backend/pre-commit.sh`
- ty hook：`backend/.pre-commit-config.yaml`
- backend CI：`.github/workflows/backend-lint.yml`

## 约束

- 用户提到 lint 错误时，必须运行 `cd backend && bash pre-commit.sh` 查看具体错误。
- 修改 lint、类型检查或 pre-commit 流程时，必须同步更新本文件与 `docs/backend/README.md`。
- backend CI 的 Postgres 和 Redis 由 GitHub Actions services 提供；对象存储在 workflow 中启动；不通过 docker compose 启动依赖服务。
- 后端 pre-commit 配置避免依赖远程 hook 仓库；ruff、mypy、pyright、ty、uv lock 和 uv export 均通过本地命令运行。
