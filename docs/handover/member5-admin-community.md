# 成员 5：管理端与社区交接

## 1. 管理端目录与现有页面

```text
frontend-admin/
├─ src/main.ts
├─ src/App.vue
├─ src/router/index.ts
├─ src/services/api.ts
├─ src/views/
│  ├─ LoginView.vue
│  ├─ DashboardView.vue
│  ├─ CultureManageView.vue
│  └─ PlaceholderView.vue
├─ src/env.d.ts
├─ src/styles.css
├─ tsconfig.json
└─ vite.config.ts
```

路由：`/login`、`/` 看板、`/cultures` 文化管理；`/routes`、`/templates`、`/posts` 目前使用占位页，分别预留给成员 4、3、5。路由守卫检查 `localStorage.adminAccessToken`。

## 2. API 入口与社区骨架

- 管理端 Axios：`frontend-admin/src/services/api.ts`，默认 `/api/v1`。
- 社区后端：`backend/app/api/community.py`、`models/community.py`、`schemas/community.py`。
- 后台后端：`backend/app/api/admin.py`。
- 管理入口：`GET /api/v1/admin/dashboard`、`GET /api/v1/admin/users`、`PATCH /api/v1/admin/posts/{id}/review`、`POST /api/v1/admin/users/{id}/points`。

社区目前具备帖子列表/详情/发布/更新/删除、评论列表/发布、点赞幂等和收藏切换的基础 API 骨架；创建帖子、点赞和重复点赞已经通过真实 MySQL 验证。详细表、参数、响应和规则以 `docs/handover/member5-community.md` 为唯一社区交接基准，本文件不替代它。

## 3. 未完成能力

- 收藏只有后端基础切换入口，收藏列表、状态展示和完整产品规则未完成。
- 社区审核只有基础管理 API，审核队列、操作记录和管理页面未完成。
- 举报、活动、排行均未实现。
- 社区用户端和管理端的完整页面、筛选、分页反馈、空状态尚未完成。
- 标签运营、敏感内容策略、申诉和通知未形成完整流程。

成员 5 应在既有骨架上继续，避免让成员 1 代做完整社区业务。

## 4. 检查与构建

```powershell
pnpm --dir frontend-admin exec vue-tsc --noEmit
pnpm --dir frontend-admin run build
```

当前管理端已实际通过类型检查和生产构建。`tsconfig.json` 使用 `skipLibCheck` 避免第三方 Element Plus 声明兼容错误，项目源码仍使用严格模式。

## 5. 冲突文件和分支

潜在冲突：`frontend-admin/src/router/index.ts`、`App.vue`、`services/api.ts`、`styles.css`、`PlaceholderView.vue`，以及 `backend/app/api/community.py`、`admin.py`、社区 Schema/Model 和任何 Alembic 迁移。不得直接改公共响应或认证依赖。

推荐分支：`feature/member5-admin-community`；若后台和社区改动较大，可拆为 `feature/member5-community` 与 `feature/member5-admin-ui` 两个短分支。

## 6. 验收标准

- 管理端类型检查、生产构建通过。
- 普通用户访问管理 API 得到 403，管理员操作成功。
- 社区关键写操作有鉴权、明确错误和幂等行为。
- 收藏、审核、举报、活动、排行按 Issue 分批实现，不混入公共架构 PR。
- API 保持 `/api/v1` 与统一响应契约；数据库变更由成员 1 审核迁移。
- PR 提供管理端截图、接口测试和与 `member5-community.md` 的完成项对照。
