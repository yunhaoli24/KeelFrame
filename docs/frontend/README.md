# 前端文档索引

前端位于 `frontend/`，全栈联调统一通过仓库根目录 `./dev.sh` 启动。

## 开发入口

- 全栈启动：`./dev.sh`
- 前端单独启动：`cd frontend && pnpm run dev`
- 前端依赖安装：`cd frontend && pnpm install`
- 前端检查：`cd frontend && pnpm run check`
- 前端测试：`cd frontend && pnpm run test`
- 前端构建：`cd frontend && pnpm run build`

## 工具链约束

- 前端工具链使用 Vite+，`vp` 作为 `frontend` 的本地 npm 包命令运行。
- 不全局安装 `vp`；启动、检查、测试和构建通过 `pnpm run ...` 脚本间接调用 `vp`。
- 前端 Vite+、lint、format、test、staged 配置集中在 `frontend/vite.config.ts`。
- Vite/Vitest API 通过 Vite+ 入口使用：配置从 `vite-plus` 导入，测试从 `vite-plus/test` 导入。

## 代码入口

- 前端说明：`frontend/README.md`
- Vite+ 配置：`frontend/vite.config.ts`
- 包配置：`frontend/package.json`
