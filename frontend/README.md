# Frontend

这是 RBAC 全栈模板的前端管理台，负责登录、路由守卫、系统管理页面、数据表格、表单交互和后端 API 调用。

## 当前定位

- 提供后台管理系统的基础布局、侧边栏、导航、主题和错误页。
- 提供用户、角色、菜单、部门、数据权限等 RBAC 管理页面。
- 提供登录流程、认证状态管理和路由访问控制。
- 提供统一 API 服务目录，便于业务模块继续扩展。
- 作为后续业务系统的前端壳子，业务页面应沿用当前页面、服务、组件和状态管理结构。

## 目录入口

```text
frontend/
├── src/pages/             # 页面路由入口
├── src/pages/system/      # RBAC 与系统管理页面
├── src/services/api/      # 后端 API 调用封装
├── src/components/        # 通用组件和业务组件
├── src/composables/       # 组合式逻辑
├── src/stores/            # Pinia 状态
├── src/router/            # 路由与守卫
└── src/plugins/           # 前端插件初始化
```

## 开发入口

- 全栈启动：在仓库根目录运行 `./dev.sh`
- 前端单独启动：`pnpm run dev`
- 前端检查：`pnpm run check`
- 前端测试：`pnpm run test`
- 前端构建：`pnpm run build`

## 约束

- API 调用优先放在 `src/services/api/`，页面通过服务层访问后端。
- 新增页面优先复用现有布局、数据表格、表单和对话框组件。
- 认证相关逻辑集中维护在 `src/stores/auth.ts`、`src/composables/use-auth.ts` 和 `src/router/guard/`。
- 新增模板能力时，同步补齐页面、服务封装和前端测试。
