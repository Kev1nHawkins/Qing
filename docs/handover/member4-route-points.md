# 成员 4：路线、任务与积分交接

## 1. 相关模型

- `Location`：地点名称、地址、说明、经纬度和文化条目关联。
- `Route`：路线标题、slug、摘要、封面、时长、距离、发布状态。
- `RouteTask`：路线顺序、地点、文化条目、任务类型、问答/二维码/坐标、积分。
- `UserTaskRecord`：用户任务进度、答案、校验结果、完成时间和已授积分。
- `PointRecord`：积分变动、余额、原因、业务幂等键。
- `Badge`、`UserBadge`：徽章规则和用户授予记录。

代码集中在 `backend/app/models/culture.py`、`route.py`、`points.py`，Schema/API 位于同名领域文件。

## 2. 现有 API

- 地点：`GET/POST /api/v1/locations`，`GET/PUT/DELETE /api/v1/locations/{id}`。
- 路线：`GET/POST /api/v1/routes`，`GET/PUT/DELETE /api/v1/routes/{id}`，`POST /api/v1/routes/{id}/start`。
- 任务：`GET/POST /api/v1/tasks`，`GET/PUT/DELETE /api/v1/tasks/{id}`，`POST /api/v1/tasks/{id}/complete`。
- 积分：`GET /api/v1/points/summary`、`GET /api/v1/points/records`。
- 徽章：`GET /api/v1/badges`、`GET /api/v1/badges/mine`、`POST /api/v1/badges`。

管理类写接口要求管理员权限。

## 3. 已实现的幂等规则

- `user_task_records(user_id, task_id)` 唯一，同一用户对同一任务只保留一条记录。
- 完成接口发现 `COMPLETED` 记录时返回 `alreadyCompleted: true`，不再次加分。
- 积分使用 `point_records(user_id, business_key)` 唯一键，任务业务键为 `task:{task_id}`。
- `POST /routes/{id}/start` 重复调用复用首任务记录并返回 `alreadyStarted`。

重复完成任务不重复加分已经通过真实 MySQL 8.4 验证。

## 4. 当前种子数据

`backend/app/scripts/seed.py` 幂等创建 `kapok-trail`（红棉寻迹）演示路线、一个文化条目、五个校园地点和五个任务节点。节点类型依次覆盖签到、问答、二维码、模拟位置和签到，每项默认 10 分；同时创建三个徽章规则。实际名称以 UTF-8 源文件和数据库结果为准。

## 5. 后续任务边界

成员 4 可继续实现地图 SDK 展示、路线详情、地理围栏校验、真实定位授权、二维码扫描、打卡反馈、路线进度和徽章授予。不得私自改变坐标精度、任务类型、积分唯一键或现有 API 路径；结构变更先交成员 1 审核。

与成员 2 联调：路线列表/详情、地点列表、开始路线、任务提交、积分概览/流水、徽章列表/我的徽章；要明确定位拒绝、答案错误、重复完成和离线场景。

## 6. 冲突文件、分支与验收

潜在冲突：`backend/app/api/router.py`、`backend/app/api/route.py`、`task.py`、`location.py`、`points.py`、`badge.py`、对应 Schema/Model、`seed.py`、迁移文件，以及用户端 `src/router/index.ts`。公共文件改动需拆小 PR。

推荐分支：`feature/member4-route-points`。

验收标准：地图与定位权限处理清晰；任务类型校验真实有效；重复开始/完成不重复写记录或加分；积分流水余额一致；路线和任务在用户端完成真实联调；新增迁移经成员 1 审核；类型检查、后端测试和 Swagger 契约通过。
