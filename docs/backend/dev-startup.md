# 全栈开发启动与进程管理

## 结论

- 全栈开发统一通过根目录脚本 `./dev.sh` 启动。
- `dev.sh` 会同时拉起前端、后端 API、Celery worker、Celery beat、Celery flower。
- `dev.sh` 会自动探测后端 API 和 flower 可用端口，并在服务退出时统一回收子进程。
- `dev.sh` 只负责启动应用进程；本地 `.env` 与 Docker 依赖服务由开发者手动准备。

## 入口

- 启动命令：`./dev.sh`
- 脚本位置：`dev.sh`

## 约束

- 修改 `dev.sh` 时必须保留端口冲突处理与多进程统一清理逻辑。
- 不在 `dev.sh` 中自动创建 `.env`，也不自动启动 Postgres、Redis、RabbitMQ 等 Docker 服务。
- 本地联调优先复用该脚本，不在文档中分散维护多套启动流程。
