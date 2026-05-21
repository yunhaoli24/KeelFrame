# 后端 lint、pyright 与 ty 约束

## 结论

- 后端质量检查统一从 `backend/` 目录运行 `bash backend/scripts/lint.sh`。
- lint 脚本入口为 `backend/backend/scripts/lint.sh`。
- `backend/pre-commit.sh` 复用同一个 lint 脚本。
- pre-commit 使用项目本地环境运行 `uv run ty check`。
- pre-commit hooks 统一使用 `repo: local` 和项目本地工具。

## 入口

- 运行命令：`cd backend && bash backend/scripts/lint.sh`
- 脚本位置：`backend/backend/scripts/lint.sh`
- pre-commit 入口：`backend/pre-commit.sh`
- ty hook：`backend/.pre-commit-config.yaml`

## 约束

- 用户提到 lint 错误时，必须运行 `cd backend && bash backend/scripts/lint.sh` 查看具体错误。
- 修改 lint、类型检查或 pre-commit 流程时，必须同步更新本文件与 `docs/backend/README.md`。
- 后端 pre-commit 配置避免依赖远程 hook 仓库；ruff、mypy、pyright、ty、uv lock 和 uv export 均通过本地命令运行。
