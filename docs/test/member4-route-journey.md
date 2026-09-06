# 成员4：校园寻迹、地图与积分徽章联调记录

## 交付范围

- 用户端正式入口：`/routes`。
- 三条路线：红棉寻迹、建筑寻纹、湖畔拾光。
- 路线地图：配置高德地图浏览器端 Key 时使用高德 JS API；未配置或网络异常时自动降级为离线校园示意图。
- 地图标记、路线折线、路线切换、任务时间线和任务详情。
- 文化问答和图片打卡；所有非问答任务统一上传现场图片，不请求定位，也不扫描二维码。
- 路线领取、进度保存、积分流水、九枚徽章的分级进度和队列式解锁动画。
- 已核对第一阶段约定：红棉寻迹五个任务依次对应醒狮文化、羊城知识、广州体育、十三行商贸和广州革命记忆文化令牌；本阶段不改成员2页面结构。
- 个人图片足迹、积分动态、路线完成证书和积分商城。
- 积分商城提供 6 类 18 件好物，覆盖数字内容、导览权益、文化文创、校园限定、共创权益和文化体验。
- 任务重复完成保持幂等，不重复增加积分。

## 高德地图配置

1. 在高德开放平台的应用管理中创建应用并添加 `Web端(JS API)` Key。
2. 将项目根目录 `.env.example` 复制为 `.env`。
3. 在项目根目录 `.env` 填写：

```dotenv
VITE_AMAP_KEY=你的高德地图浏览器端Key
VITE_AMAP_SECURITY_CODE=你的高德地图 Web 端安全密钥
```

前端读取入口位于 `frontend-user/src/views/map/CampusMap.vue` 的 `loadAmap()`；Compose 透传入口位于根目录 `docker-compose.yml` 的 `frontend-user.environment`。

配置后重建用户端容器：

```powershell
docker compose up -d --build frontend-user
```

不填写 Key 也能完成比赛主流程，页面会显示离线校园示意图。

## 接口联调

所有接口使用 `/api/v1` 前缀和统一响应。

| 能力 | 接口 |
|---|---|
| 路线列表/详情 | `GET /routes`、`GET /routes/{id}` |
| 路线领取/进度/个人图片足迹 | `POST /routes/{id}/start`、`GET /routes/{id}/progress` |
| 地点 | `GET /locations` |
| 任务完成 | `POST /tasks/{id}/complete` |
| 图片打卡 | `POST /tasks/{id}/evidence` |
| 积分 | `GET /points/summary`、`GET /points/records` |
| 积分商城 | `GET /points/shop`、`POST /points/redeem`、`GET /points/redemptions` |
| 徽章 | `GET /badges`、`GET /badges/mine` |

图片接口只接受 JPG、PNG、WebP，大小不超过 8 MB。上传文件由后端保存，前端只提交后端返回的 URL。

## 已验证结果

- 路线数量：3。
- 当前联调库任务节点：15；干净种子库不少于 11，满足至少 8 个节点要求。
- 当前联调库任务类型：8 个图片打卡、7 个文化问答、0 个二维码、0 个定位。
- 红棉寻迹：5/5 完成，进度 100%。
- 红棉寻迹积分：75，产生 5 条积分流水。
- 新用户完成红棉寻迹 5 个任务并持有 75 积分时达标徽章：5 枚；完整目录共 9 枚。
- 重复完成首任务：`alreadyCompleted=true`，总积分保持 75。
- 图片上传后可通过 `/uploads/task-checkins/...` 访问。
- 冒烟测试：27/27 通过，包含缺图拒绝、伪造图片拒绝、图片上传、个人图片足迹、任务幂等、商城目录、真实扣分、重复兑换幂等和兑换凭证查询。
- 本轮徽章/奖励专项测试：3/3 通过；用户端生产构建通过。
- 390 px 移动端宽度无横向溢出。

## 人工验收步骤

1. 打开 `http://localhost:5173/routes/journey`，确认显示三条路线。
2. 分别切换三条路线，确认地图标记和任务时间线同步更新。
3. 登录后领取“红棉寻迹”，完成文化问答和图片打卡任务。
4. 刷新页面，确认任务进度保留。
5. 检查积分流水、徽章进度、解锁率和连续解锁反馈。
6. 重复提交已完成任务，确认积分不变。
7. 在积分商城切换商品分类，选择积分足够的商品并打开兑换确认弹窗。
8. 确认兑换后检查余额与积分流水；使用同一兑换请求重试时不得重复扣分。
9. 打开“我的兑换”，检查分类、兑换状态、兑换码、领取方式和兑换时间。
10. 检查商城概览的奖励总数、分类数、可重复兑换数与当前可兑数是否和目录一致。

## 第二阶段补强与验证

### 变更

- `docker-compose.yml` 已向用户端容器透传 `VITE_AMAP_KEY` 和
  `VITE_AMAP_SECURITY_CODE`；空值不会阻断启动。
- 高德脚本加载增加 8 秒超时和加载状态复用。未配置 Key、脚本失败、初始化失败或
  连接超时时统一切换离线校园示意图。
- 已核对五枚文化令牌与 `kapok-trail` 五个任务的顺序、积分流水和徽章规则。
  本阶段不新增令牌 UI、API 或数据库字段，避免覆盖成员2页面和重复实现第一阶段 PR。

### 自动化与运行态证据

```text
docker compose exec -T backend pytest -q tests/test_member4_route_points.py
2 passed

docker compose exec -T backend pytest -q
44 passed

docker compose exec -T frontend-user npm run build
vue-tsc + vite build passed

docker compose exec -T frontend-admin npm run build
vue-tsc + vite build passed（仅保留既有的大包体积警告）
```

真实 MySQL/HTTP 验证使用新注册测试用户完成一次图片任务和一次奖励兑换：

```text
路线：kapok-trail
图片资源归属上传：成功
首次任务奖励：+10
重复完成：alreadyCompleted=true
任务积分流水：1 条
首次兑换：10 积分，余额 10 -> 0
重复兑换：alreadyRedeemed=true
兑换记录：1 条，已生成兑换凭证
```

浏览器运行态验证：

- 配置高德 Web JS API Key 和安全密钥后显示“高德地图实时校园路线”，5 个任务标记正常加载。
- 空地图 Key 时显示“已切换为离线校园示意图”，5 个任务节点均可见，控制台无错误。
- 脚本加载错误、初始化失败或 8 秒超时与空 Key 共用同一离线降级视图，不阻断任务主流程。
- 390 px 视口下 `scrollWidth == clientWidth`，现有路线页面无横向溢出。

完整配置、GitHub Actions 注入和降级验收说明见
`docs/deployment/amap-web-js.md`。

### 变更边界

- API 路径和统一响应结构：无变化。
- 数据库模型、字段和 Alembic：无变化。
- 用户端公共路由和现有页面结构：无变化。
- 未新增支付、物流、地址或商业订单能力。
- 公共文件：`docker-compose.yml` 仅新增两个地图环境变量透传项，合并前需由成员1复核。
