# 对象存储与静态文件

## 结论

- 后端上传接口默认使用 S3 兼容对象存储，不再把用户上传文件写入本地 `static/upload`。
- 后端不再挂载 `/static`，仓库内不保留 `backend/backend/static/` 静态文件目录。
- 后端内置只读资源放在 `backend/backend/resources/`，例如 `ip2region_v4.xdb`。
- 本地 Docker 依赖服务使用 `docker-compose.yml` 中的 `fba_rustfs` 提供对象存储，默认 bucket 为 `fba-static`。
- 前端只访问后端返回的文件 path URL，由后端 `GET` 接口完成权限校验后转发到对象存储；S3/RustFS endpoint 仅后端内部使用。

## 入口

- 默认对象存储配置：`backend/backend/.env`
- 默认对象存储上传服务：`backend/backend/app/s3/service/object_storage.py`
- 系统文件上传接口：`backend/backend/app/admin/api/v1/sys/file.py`
- S3 文件上传接口：`backend/backend/app/s3/api/v1/file.py`
- 本地 RustFS Docker 服务：`docker-compose.yml`

## 约束

- 新增上传能力时，优先复用默认对象存储配置，不再引入本地静态目录落盘链路。
- 用户可访问文件 URL 必须返回后端 API 地址，不直接暴露对象存储地址。
- 文件读取只保留后端 path 代理接口，不保留 query 下载兼容入口。
- 黑盒 API 测试应通过真实 HTTP 接口验证对象存储上传行为，不直接 mock 内部存储函数。
