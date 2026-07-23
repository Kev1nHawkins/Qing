# 角色 5 社区模块交接

> 当前状态：**基础骨架已完成，后续完整社区业务由角色 5 负责。**
>
> 角色 1 仅维护数据库迁移、鉴权、统一响应、Swagger 契约和部署稳定性，不继续扩展社区业务规则或前端页面。

## 1. 当前数据库表

| 表 | 作用 | 关键约束 |
|---|---|---|
| `posts` | 社区帖子，可关联作者、文化条目和 AI 作品 | `author_id` 必填；缓存点赞、评论、收藏计数 |
| `comments` | 帖子评论及一级父评论引用 | `post_id`、`user_id` 必填；`parent_id` 可空 |
| `post_likes` | 用户点赞关系 | `(post_id, user_id)` 唯一，防止重复点赞 |
| `favorites` | 用户收藏关系 | `(post_id, user_id)` 唯一 |
| `tags` | 社区标签字典 | `name`、`slug` 唯一 |
| `post_tags` | 帖子与标签关联 | `(post_id, tag_id)` 唯一 |

相关外键还包括 `users`、`culture_items`、`ai_creations`。初始结构由
`backend/alembic/versions/20260723_0001_initial_schema.py` 管理；角色 5 不应直接修改已执行迁移。

## 2. 当前 API 路径

统一前缀：`/api/v1/community`。

| 方法 | 路径 | 鉴权 | 当前作用 |
|---|---|---|---|
| GET | `/posts` | 否 | 分页查询已发布帖子 |
| GET | `/posts/{post_id}` | 否 | 查询帖子详情 |
| POST | `/posts` | 是 | 发布基础帖子 |
| PUT | `/posts/{post_id}` | 是 | 作者或管理员更新帖子 |
| DELETE | `/posts/{post_id}` | 是 | 作者或管理员删除帖子 |
| GET | `/posts/{post_id}/comments` | 否 | 查询未删除评论 |
| POST | `/posts/{post_id}/comments` | 是 | 发表评论 |
| POST | `/posts/{post_id}/like` | 是 | 幂等点赞 |
| POST | `/posts/{post_id}/favorite` | 是 | 收藏/取消收藏骨架 |

Swagger 运行地址：`http://localhost:8000/docs`。实际 OpenAPI JSON：
`http://localhost:8000/openapi.json`。

## 3. 请求参数和响应格式

所有响应统一为：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "requestId": "uuid"
}
```

分页列表请求：

```text
GET /posts?page=1&pageSize=20&culture_item_id=1
```

列表 `data`：

```json
{
  "total": 1,
  "items": [],
  "page": 1,
  "pageSize": 20
}
```

创建帖子 `POST /posts`：

```json
{
  "title": "红棉寻迹作品",
  "content": "帖子正文",
  "culture_item_id": 1,
  "creation_id": null,
  "cover_image_url": null,
  "tags": ["木棉", "校园文化"]
}
```

更新帖子 `PUT /posts/{post_id}`：

```json
{
  "title": "可选的新标题",
  "content": "可选的新正文",
  "cover_image_url": "可选图片地址"
}
```

创建评论 `POST /posts/{post_id}/comments`：

```json
{
  "content": "评论内容",
  "parent_id": null
}
```

点赞 `POST /posts/{post_id}/like` 无请求体。首次返回：

```json
{
  "liked": true,
  "likeCount": 1,
  "alreadyLiked": false
}
```

相同用户再次点赞不会重复计数，返回 `alreadyLiked: true`。收藏接口无请求体，
当前返回 `favorited` 和 `favoriteCount`。

常见错误：未登录 `401`、无权限 `403`、资源不存在 `404`、数据冲突 `409`、
参数错误 `422`。错误仍使用统一响应结构。

## 4. 当前业务规则

- 列表仅展示 `PUBLISHED` 帖子。
- 当前基础发布接口直接将帖子设为 `PUBLISHED`，尚未形成完整审核流。
- 帖子可选关联一个文化条目和一个 AI 作品。
- 作者或管理员可修改、删除帖子。
- 评论列表过滤逻辑删除记录；评论创建会增加帖子评论计数。
- 点赞通过数据库唯一约束和接口判断双重保证幂等。
- 收藏关系存在基础切换接口，尚未进行完整产品化。
- 帖子计数为冗余字段，后续并发一致性方案需要角色 5 评审。

## 5. 当前未实现

- 完整帖子审核工作流、审核记录与审核后台。
- 举报、屏蔽、敏感词、风控和申诉。
- 热门排行、推荐流、关注流和搜索。
- 活动、话题运营和社区任务。
- 评论编辑、删除接口、楼中楼展示和通知。
- 分页评论、批量运营、内容导出。
- 社区完整用户端页面及管理端页面。
- 并发计数校准、缓存、限流和社区专项测试。

这些内容均不属于角色 1 当前交付范围。

## 6. 建议角色 5 后续任务

1. 先确认比赛 MVP 的帖子审核和下架流程。
2. 为现有帖子、评论、点赞接口补充单元测试和真实 MySQL 集成测试。
3. 完成用户端社区信息流、发布页和帖子详情页。
4. 完成管理端帖子列表与最小审核操作。
5. 评审计数字段的并发更新策略和数据修复脚本。
6. 补充演示帖子数据、截图、测试证据和接口文档。

收藏、排行、举报、活动等功能应单独建 Issue，经项目负责人确认优先级后再开发。

## 7. 主要代码目录

```text
backend/app/api/community.py
backend/app/models/community.py
backend/app/schemas/community.py
frontend-user/src/views/CommunityView.vue
frontend-admin/src/views/PlaceholderView.vue
docs/handover/member5-community.md
```

共享注册文件：

```text
backend/app/api/router.py
backend/app/models/__init__.py
frontend-user/src/router/index.ts
frontend-admin/src/router/index.ts
```

## 8. 注意事项和潜在 Git 冲突

- `backend/alembic/versions/` 仅由角色 1 生成迁移，角色 5 先提 Issue，不直接新建或改迁移。
- `backend/app/api/router.py`、`backend/app/models/__init__.py` 是多人共享文件，修改前同步。
- 两个前端的 `package.json`、路由文件和请求封装属于高冲突文件。
- 不改变现有 `/api/v1/community` 路径和统一响应结构。
- 不把 AI Key、数据库密码、`.env` 或个人绝对路径提交到仓库。
- 更新计数、点赞和审核规则时必须验证重复请求及并发行为。

## 9. 推荐 feature 分支

```text
feature/member5-community-feed
feature/member5-community-publish
feature/member5-community-admin
fix/member5-community-counter-idempotency
```

一项功能一个分支，PR 目标为 `develop`。

## 10. 验收标准

- 社区主流程“查看帖子 → 发布 → 评论 → 点赞”可在真实 MySQL 连续执行三次。
- 同一用户重复点赞不重复计数。
- 非作者不能修改或删除他人帖子，管理员权限行为有测试证据。
- 帖子必须能够关联文化条目；AI 作品发布仅对接既有作品 ID。
- 所有接口出现在 Swagger，使用统一响应和 `requestId`。
- 用户端常见移动宽度无横向溢出；管理端最小审核流程可演示。
- PR 包含接口变更、测试步骤、截图或录屏、风险与待办。
- 不修改既有数据库字段或 API 路径；如确需变更，先建 Issue 并由角色 1 生成迁移。

