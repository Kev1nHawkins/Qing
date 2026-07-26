# 成员4新增 API 审核提案

> 状态：待成员1审核。无数据库结构或 Alembic 变更。

所有 JSON 接口继续使用 `/api/v1` 和 `{code,message,data,requestId}`。

## 路线进度

`GET /api/v1/routes/{route_id}/progress`

- 权限：登录用户。
- 仅允许已发布路线。
- 返回当前用户的任务完成数量、任务 ID、积分和图片资产 ID。
- 不返回问答答案、二维码答案或文件系统路径。
- 公共路线/任务列表与详情只返回已发布数据。

## 任务图片凭证

`POST /api/v1/tasks/{task_id}/evidence`

- 权限：登录用户。
- 请求体：原始图片字节，`Content-Type` 为 `image/jpeg`、`image/png` 或 `image/webp`；可选 `X-File-Name`。
- 仅已领取路线中的 `CHECK_IN` 任务可上传。
- 按用户串行检查上传数量，每个任务最多保留 5 个凭证。
- 服务端流式读取并在超过 8 MB 时立即终止，不经过 multipart 解析器。
- 返回 `FileAsset.id`；完成任务时通过 `file_asset_id` 引用。
- 存储根目录读取 `LINGCHAO_UPLOAD_ROOT`；未配置时使用当前工作目录下的 `uploads`。Docker 环境继续复用现有 `uploads_data:/app/uploads` 持久化卷。

`GET /api/v1/tasks/{task_id}/evidence/{asset_id}`

- 权限：登录用户。
- 同时验证资产所有者和任务绑定关系。
- 响应图片设置 `X-Content-Type-Options: nosniff` 和私有缓存。

`POST /api/v1/tasks/{task_id}/complete` 请求扩展：

```json
{
  "answer": "问答答案",
  "qr_code": "二维码内容",
  "latitude": 23.0,
  "longitude": 113.0,
  "file_asset_id": 123
}
```

后端只读取与任务类型匹配的字段。

## 积分商城

- `GET /api/v1/points/shop`：公开商品目录。
- `POST /api/v1/points/redeem`：登录用户兑换，支持请求幂等。
- `GET /api/v1/points/redemptions`：当前用户兑换记录。

兑换请求：

```json
{
  "product_code": "kapok-wallpaper",
  "redemption_id": "client-generated-id"
}
```

兑换复用 `point_records`，`business_key` 格式为 `redeem:{product_code}:{redemption_id}`。事务先锁用户行，再检查重复请求、一次性限兑和余额，避免并发重复扣款。
