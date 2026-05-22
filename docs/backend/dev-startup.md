# 全栈开发启动与进程管理

## 结论

- 全栈开发统一通过根目录脚本 `./dev.sh` 启动。
- `dev.sh` 会先执行后端数据库迁移与基线数据迁移，再启动应用进程。
- `dev.sh` 会同时拉起前端、后端 API、Celery worker、Celery beat、Celery flower。
- `dev.sh` 会自动探测后端 API 和 flower 可用端口，并在服务退出时统一回收子进程。
- `dev.sh` 只负责启动应用进程；本地 `.env` 与 Docker 依赖服务由开发者手动准备。
- 对象存储本地依赖通过根目录 `docker-compose.yml` 中的 `fba_rustfs` 提供，不由 `dev.sh` 自动启动。
- Docker 部署入口由前端 Nginx 容器 `fba_ui` 提供，负责托管前端构建产物并反代后端 API。

## 入口

- 启动命令：`./dev.sh`
- 脚本位置：`dev.sh`
- 数据库迁移命令：`cd backend && uv run fba migrate`
- 迁移配置目录：`backend/backend/alembic/`
- Docker 依赖服务：`docker compose up -d fba_postgres fba_redis fba_rabbitmq fba_rustfs fba_rustfs_bucket_init`
- Docker 全栈入口：`docker compose up -d fba_ui`

## 约束

- 修改 `dev.sh` 时必须保留端口冲突处理与多进程统一清理逻辑。
- 不在 `dev.sh` 中自动创建 `.env`，也不自动启动 Postgres、Redis、RabbitMQ 等 Docker 服务。
- 后端 schema 与基线数据变更必须通过 Alembic revision 管理。
- 本地联调优先复用该脚本，不在文档中分散维护多套启动流程。
