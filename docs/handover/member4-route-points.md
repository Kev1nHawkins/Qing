# 成员 4：路线、任务与积分交接

## 1. 相关模型

- `Location`：地点名称、地址、说明、经纬度和文化条目关联。
- `Route`：路线标题、slug、摘要、封面、时长、距离、发布状态。
- `RouteTask`：路线顺序、地点、文化条目、任务类型、问答/图片证据、积分。
- `UserTaskRecord`：用户任务进度、答案、校验结果、完成时间和已授积分。
- `PointRecord`：积分变动、余额、原因、业务幂等键。
- `Badge`、`UserBadge`：徽章规则和用户授予记录。

代码集中在 `backend/app/models/culture.py`、`route.py`、`points.py`，Schema/API 位于同名领域文件。

## 2. 现有 API

- 地点：`GET/POST /api/v1/locations`，`GET/PUT/DELETE /api/v1/locations/{id}`。
- 路线：`GET/POST /api/v1/routes`，`GET/PUT/DELETE /api/v1/routes/{id}`，`POST /api/v1/routes/{id}/start`。
- 任务：`GET/POST /api/v1/tasks`，`GET/PUT/DELETE /api/v1/tasks/{id}`，`POST /api/v1/tasks/{id}/complete`。
- 积分：`GET /api/v1/points/summary`、`GET /api/v1/points/records`。
- 积分商城：`GET /api/v1/points/shop`、`POST /api/v1/points/redeem`、`GET /api/v1/points/redemptions`。
- 徽章：`GET /api/v1/badges`、`GET /api/v1/badges/mine`、`POST /api/v1/badges`。

管理类写接口要求管理员权限。

## 3. 已实现的幂等规则

- `user_task_records(user_id, task_id)` 唯一，同一用户对同一任务只保留一条记录。
- 完成接口发现 `COMPLETED` 记录时返回 `alreadyCompleted: true`，不再次加分。
- 积分使用 `point_records(user_id, business_key)` 唯一键，任务业务键为 `task:{task_id}`。
- `POST /routes/{id}/start` 重复调用复用首任务记录并返回 `alreadyStarted`。

重复完成任务不重复加分已经通过真实 MySQL 8.4 验证。

## 4. 当前种子数据

`backend/app/scripts/seed.py` 幂等创建三条演示路线。任务只保留文化问答和图片打卡两种交互；种子执行时会把旧二维码/定位节点更新为图片打卡，同时创建三个徽章规则。

## 5. 后续任务边界

成员 4 可继续完善地图 SDK 展示、路线详情、图片证据审核、打卡反馈、路线进度和徽章授予。不得私自改变坐标精度、积分唯一键或现有 API 路径；结构变更先交成员 1 审核。

与成员 2 联调：路线列表/详情、地点列表、开始路线、任务提交、积分概览/流水、徽章列表/我的徽章；要明确图片格式/大小、答案错误、重复完成和离线场景。

## 6. 冲突文件、分支与验收

潜在冲突：`backend/app/api/router.py`、`backend/app/api/route.py`、`task.py`、`location.py`、`points.py`、`badge.py`、对应 Schema/Model、`seed.py`、迁移文件，以及用户端 `src/router/index.ts`。公共文件改动需拆小 PR。

推荐分支：`feature/member4-route-points`。

验收标准：地图加载与降级处理清晰；图片和问答校验真实有效；重复开始/完成不重复写记录或加分；积分流水余额一致；路线和任务在用户端完成真实联调；新增迁移经成员 1 审核；类型检查、后端测试和 Swagger 契约通过。

## 7. 7月25日用户端联调更新

- `/routes` 已整合三条正式演示路线和统一校园地图工作区。
- 新增高德地图 JS API 接入，并提供无 Key/断网时的离线校园示意图兜底。
- 已接入文化问答和图片上传打卡，旧二维码/定位任务按图片打卡兼容。
- 路线进度、积分流水、徽章状态和解锁反馈均使用真实 API。
- 图片上传复用既有 `file_assets` 表，没有数据库结构变更或新增迁移。
- 详细复现步骤见 `docs/test/member4-route-journey.md`。

## 8. 管理端同步

- 管理入口：`http://localhost:4174/routes`。
- 实时汇总路线数、任务数、图片打卡数、文化问答数和配置积分。
- 支持三条路线切换与路线标题、简介、距离、时长、发布状态编辑。
- 支持任务新增、编辑和删除；新任务仅提供图片打卡与文化问答两种类型。
- 地点下拉框复用 `/api/v1/locations`，路线和任务写操作复用现有管理员 API。
- 管理端实现位于 `frontend-admin/src/views/RouteTaskManageView.vue`，没有数据库结构变更。

## 9. 积分商城

- 用户端入口位于 `/routes` 的路线工作区下方，组件为 `frontend-user/src/views/points/PointsMall.vue`。
- 当前提供 6 类 12 件商品：手机壁纸、贴纸包、电子藏书票、语音导览、书签、种子纸明信片、文化地图折页、珐琅徽章、AI 海报导出券、手作工坊预约、讲座优先席和校园帆布袋。
- 商品目录由后端返回，前端不硬编码价格；兑换通过现有 `point_records` 写入负积分流水，不新增数据库表或字段。
- 一次性商品按商品编码和用户限制重复兑换；同一 `redemption_id` 重试保持幂等，不重复扣分。
- “我的兑换”按数字权益、实体领取和体验预约分类展示，并提供状态、兑换码、领取方式和兑换时间。
- 真实 MySQL 冒烟测试为 27/27 通过，覆盖商品目录、兑换扣分、重复兑换和兑换凭证查询。
