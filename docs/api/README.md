# API 约定

基础地址：`http://localhost:8000/api/v1`

鉴权：登录后在请求头使用 `Authorization: Bearer <JWT>`。Swagger 右上角 `Authorize` 直接粘贴 JWT。

统一成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "requestId": "3f7bfe12-9bd4-4ac0-924a-65d8cbab247a"
}
```

统一失败响应：

```json
{
  "code": 42200,
  "message": "请求参数校验失败",
  "data": [{"field": "body.title", "message": "Field required"}],
  "requestId": "3f7bfe12-9bd4-4ac0-924a-65d8cbab247a"
}
```

分页请求使用 `page`、`pageSize`，返回 `total`、`items`、`page`、`pageSize`。

## 模块

| 模块 | 路径前缀 | 说明 |
|---|---|---|
| Auth | `/auth` | 注册、JWT 登录、当前用户 |
| Culture | `/cultures` | 文化条目 CRUD |
| Location | `/locations` | 校园地点 CRUD |
| Route | `/routes` | 寻迹路线 CRUD |
| Task | `/tasks` | 任务节点 CRUD、完成任务 |
| Creation | `/creations` | 模板、异步创作、状态、重试 |
| Community | `/community` | 帖子、评论、点赞、收藏 |
| Points | `/points` | 积分概览与流水 |
| Badge | `/badges` | 徽章与用户徽章 |
| Admin | `/admin` | 看板、用户、帖子审核、积分调整 |

## 社区与审核补充

社区公开接口：

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/community/posts` | 否 | 已发布信息流；支持 `page`、`pageSize`、`contentType=AI/CAMPUS/CULTURE`、`tag` |
| `GET` | `/community/posts/{post_id}` | 否 | 已发布帖子详情 |
| `POST` | `/community/posts` | 是 | 发布帖子；只能关联本人成功的 AI 作品，管理员除外 |
| `POST` | `/community/posts/{post_id}/like` | 是 | 幂等点赞；重复请求返回 `alreadyLiked=true`，计数不增加 |
| `POST` | `/community/posts/{post_id}/favorite` | 是 | 收藏切换；用户与帖子关系唯一 |
| `GET` | `/community/posts/{post_id}/comments` | 否 | 评论列表 |
| `POST` | `/community/posts/{post_id}/comments` | 是 | 发布评论；回复时校验父评论属于同一帖子 |

帖子响应在原字段上新增 `author_name`、`author_avatar_url`、
`culture_item_title`、`creation_title`、`creation_preview_url` 和 `tags`；
评论响应新增 `author_name`、`author_avatar_url`。这些均为向后兼容的可选字段。

管理接口：

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/admin/posts` | 管理员 | 审核列表；支持 `status`、`keyword`、`page`、`pageSize`，返回 `statusCounts` |
| `PATCH` | `/admin/posts/{post_id}/review` | 管理员 | 状态改为 `PUBLISHED`、`REJECTED` 或 `OFFLINE` |

本次社区闭环没有数据库结构变更，复用既有帖子、标签、点赞、评论和收藏关系。

接口和字段的唯一可执行定义是运行中的 OpenAPI：`/openapi.json`。接口变更必须先更新本目录文档并在 PR 中标注。

