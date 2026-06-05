# 前端文档索引

前端位于 `frontend/`，全栈联调统一通过仓库根目录 `./dev.sh` 启动。

## 开发入口

- 全栈启动：`./dev.sh`
- 前端单独启动：`cd frontend && pnpm run dev`
- 前端依赖安装：`cd frontend && pnpm install`
- 前端检查：`cd frontend && pnpm run check`
- 前端黑盒 E2E：`cd frontend && pnpm run test`
- 前端 E2E 覆盖率：`cd frontend && pnpm run test:coverage`
- 前端构建：`cd frontend && pnpm run build`

## 工具链约束

- 前端工具链使用 Vite+，`vp` 作为 `frontend` 的本地 npm 包命令运行。
- 不全局安装 `vp`；启动、检查、测试和构建通过 `pnpm run ...` 脚本间接调用 `vp`。
- 前端 Vite+、lint、format、staged 配置集中在 `frontend/vite.config.ts`。
- 前端黑盒 E2E 使用 Playwright，配置入口为 `frontend/playwright.config.ts`，用例位于 `frontend/e2e/`。
- E2E 不 mock 后端接口或数据；运行前要求真实后端已可访问，默认地址为 `http://localhost:8080`，可通过 `E2E_API_URL` 覆盖。
- E2E 运行时只由 Playwright 启动前端 dev server，浏览器同源访问 `/api/v1`，再由 Vite proxy 转发到 `E2E_API_URL` 指向的真实后端。
- E2E 依赖后端迁移后的基线数据、可登录管理员账号和关闭验证码；账号可通过 `E2E_USERNAME`、`E2E_PASSWORD`、`E2E_DISPLAY_NAME` 覆盖。
- E2E 覆盖率脚本见 `frontend/package.json`，配置入口见 `frontend/vite.config.ts` 与 `frontend/e2e/fixtures.ts`，覆盖率产物位于 `frontend/coverage/`。

## 代码入口

- 前端说明：`frontend/README.md`
- Vite+ 配置：`frontend/vite.config.ts`
- 包配置：`frontend/package.json`
