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
| Upload | `/uploads/images` | 鉴权图片上传，供任务图片打卡复用 |
| Admin | `/admin` | 看板、用户、帖子审核、积分调整 |

接口和字段的唯一可执行定义是运行中的 OpenAPI：`/openapi.json`。接口变更必须先更新本目录文档并在 PR 中标注。
