# 成员 2：用户端前端交接

## 1. 目录结构

```text
frontend-user/
├─ src/main.ts              # Vue/Pinia/Router 入口
├─ src/App.vue              # 应用外壳
├─ src/router/index.ts      # 用户端路由
├─ src/services/api.ts      # Axios 与统一响应类型
├─ src/stores/auth.ts       # Pinia 登录状态
├─ src/views/               # 页面
├─ src/env.d.ts             # Vite 环境类型
├─ src/styles.css
├─ vite.config.ts
└─ package.json
```

## 2. 已有路由、页面和组件

| 路由 | 页面 | 当前定位 |
|---|---|---|
| `/` | `HomeView.vue` | 首页骨架 |
| `/cultures` | `CultureView.vue` | 文化内容入口 |
| `/routes` | `RouteView.vue` | 路线入口 |
| `/community` | `CommunityView.vue` | 社区基础入口 |
| `/profile` | `ProfileView.vue` | 个人中心入口 |
| `/login` | `LoginView.vue` | 登录 |

目前以页面级组件为主，尚未形成独立的 `components/` 组件库。新增公共组件前先与成员 2 确认命名和复用范围。

## 3. API 与状态管理

- 请求封装：`frontend-user/src/services/api.ts`。
- 默认 `baseURL`：`VITE_API_BASE_URL`，未设置时使用 `/api/v1`。
- Axios 自动读取 `localStorage.accessToken` 并添加 Bearer Token。
- Pinia：`frontend-user/src/stores/auth.ts`，提供 `login`、`fetchMe`、`logout`。
- 后端响应契约：`{code, message, data, requestId}`。

前端只允许保存短期访问令牌，不得放置 AI Key、数据库密码或后端密钥。

## 4. 检查和构建

标准命令：

```powershell
pnpm --dir frontend-user exec vue-tsc --noEmit
pnpm --dir frontend-user run build
```

当前环境已实际通过类型检查和 Vite 生产构建，产物为 `frontend-user/dist`；`dist` 不提交 Git。

## 5. 已完成与未完成

已完成：Vue 3/Vite/TypeScript/Pinia 骨架、六个路由入口、JWT 请求拦截、登录状态 Store、文化/路线/社区/个人中心页面骨架、生产构建验证。

未完成：完整视觉设计、响应式细节、文化详情路由、路线详情和任务交互、AI 创作页、社区完整交互、徽章展示、错误/空状态体系、真实浏览器联调。不要在公共路由文件中一次性堆叠大改动。

## 6. 跨成员联调点

- 成员 3：`/api/v1/creations/templates`、`/api/v1/creations`、`/api/v1/creations/{id}`，以及未来文化问答契约。
- 成员 4：`/api/v1/locations`、`/api/v1/routes`、`/api/v1/routes/{id}`、`/start`、`/api/v1/tasks/{id}/complete`、`/api/v1/points/*`、`/api/v1/badges/*`。
- 成员 5：`/api/v1/community/posts`、评论、点赞等基础接口。社区业务详情以 `docs/handover/member5-community.md` 为准。

## 7. 潜在冲突文件与分支

高冲突文件：`src/router/index.ts`、`src/App.vue`、`src/services/api.ts`、`src/styles.css`、`package.json`。涉及它们时拆小提交并提前通知相关成员。

推荐分支：`feature/member2-user-frontend`。

## 8. 验收标准

- 类型检查和生产构建退出码为 0。
- 不在前端保存任何真实密钥。
- API 保持 `/api/v1` 和统一响应契约。
- 登录态、401/403、加载/错误/空状态有明确表现。
- 与成员 3、4、5 的页面只消费已确认契约，不擅自改后端路径。
- PR 包含页面截图、测试路径及影响的公共文件说明。
