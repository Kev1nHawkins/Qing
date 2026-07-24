# 岭潮共创一页式集成清单

> 基线：`develop@151ee3d`。统一前缀 `/api/v1`，响应 `{code,message,data,requestId}`。状态：✅ 已有验证证据；🟡 骨架存在/待成员联调；🔴 契约未定或阻塞。任何 API 路径、公共响应、字段或表结构变更先建 Issue，由角色 1 审核；数据库变更仅由角色 1 生成 Alembic 迁移。

| 主流程步骤 | 前端页面 | 后端接口 | 核心数据表 | 主责成员 | 当前状态 | 联调前置条件 | 验收方法 | 阻塞项 | 角色1审核 |
|---|---|---|---|---|---|---|---|---|---|
| 1. 文化探索 | 用户端 `/cultures`；详情页待补 | `GET /cultures`、`GET /cultures/{id}` | `culture_items`、`file_assets` | 成员2页面；成员1基础API | ✅ API真实MySQL已验证；🟡详情交互待成员2 | 种子文化存在；Axios Base URL为`/api/v1` | 列表进入详情，空态/错误态明确；请求含`requestId` | 用户端详情路由和视觉未完成 | 是：文化字段、分页和路径 |
| 2. AI问答 | 用户端AI问答入口待建 | 🔴 尚无问答专用契约；可读取`GET /cultures/{id}`作为上下文 | `culture_items`；会话/消息是否落库待定 | 成员3；成员2接页面 | 🔴 Provider、Prompt和接口未实现 | 成员3先提交请求/响应、流式策略、超时与降级设计 | 围绕指定文化条目连续问答；Key不出后端；失败可降级 | API路径、是否新增表、模型服务网络 | **必须**：新API与任何新表 |
| 3. 路线领取 | 用户端 `/routes`；路线详情/地图待补 | `GET /routes`、`GET /routes/{id}`、`POST /routes/{id}/start`、`GET /locations` | `routes`、`route_tasks`、`locations`、`user_task_records` | 成员4；成员2接页面 | ✅ 列表/详情/开始已验证；🟡地图交互待实现 | 登录；种子路线`kapok-trail`及任务节点存在 | 领取后返回`alreadyStarted`；重复领取不重复建记录 | 地图SDK、定位授权、路线详情UI | 是：路径、坐标精度、进度字段 |
| 4. 任务完成 | 路线详情/任务面板待补 | `GET /tasks/{id}`、`POST /tasks/{id}/complete` | `route_tasks`、`user_task_records`、`point_records` | 成员4；成员2接页面 | ✅ 完成及重复完成幂等已验证；🟡真实定位/扫码待实现 | 已开始路线；按任务类型准备答案、二维码或定位 | 首次完成加分；重复完成`alreadyCompleted=true`且不重复加分 | 地理围栏、二维码扫描、错误反馈 | **必须**：校验规则、幂等键、字段变更 |
| 5. 积分 | 个人中心 `/profile` 待完善 | `GET /points/summary`、`GET /points/records` | `point_records`、`users` | 成员4；成员2接页面 | ✅ 积分及流水已验证；🟡展示待联调 | 完成任务产生流水；JWT有效 | 总分与流水余额一致；刷新后保持 | 排行不在当前范围 | 是：积分来源、人工调整和幂等策略 |
| 6. AI生成 | 用户端创作页待建；管理端`/templates`占位 | `GET/POST/PUT /creations/templates`、`POST/GET /creations`、`GET /creations/{id}`、`POST /creations/{id}/retry` | `creation_templates`、`ai_creations` | 成员3；成员2接用户端 | 🟡 API/状态骨架存在；🔴外部生成与异步处理未实现 | 模板数据；后端环境提供Key；明确`PENDING→PROCESSING→SUCCESS/FAILED` | 提交后可轮询状态；成功返回作品；失败可安全重试 | Provider、文生图网络、对象存储 | **必须**：状态机、回调/轮询契约、新字段 |
| 7. 社区发布 | 用户端 `/community` 骨架 | `GET /community/posts`、`GET /community/posts/{id}`、`POST /community/posts` | `posts`、`tags`、`post_tags`、`culture_items`、`ai_creations` | 成员5；成员2接页面 | ✅ 创建帖子基础链路已验证；🟡完整发布页待实现 | 登录；文化或成功AI作品ID可选关联 | 发布后列表/详情可见；无权限写操作被拒绝 | 上传、完整标签体验、页面反馈 | 是：公共鉴权、作品关联、Schema变更 |
| 8. 点赞评论 | 社区详情页待补 | `GET/POST /community/posts/{id}/comments`、`POST /community/posts/{id}/like` | `comments`、`post_likes`、`posts` | 成员5；成员2接页面 | ✅ 点赞与重复点赞幂等已验证；🟡评论端到端待联调 | 已登录且帖子存在 | 重复点赞计数不增长；评论列表与发布一致 | 评论UI、并发计数专项验证 | 是：权限、计数/唯一键；举报等新功能另建Issue |
| 9. 徽章 | 个人中心徽章区待补 | `GET /badges`、`GET /badges/mine` | `badges`、`user_badges`、`point_records` | 成员4；成员2接页面 | 🟡 三个种子徽章和查询API已有；自动授予待实现 | 明确授予规则与触发时机；用户完成目标 | 达标仅授予一次；“我的徽章”刷新可见 | 自动授予服务与规则验收 | **必须**：规则字段、触发逻辑、新迁移 |
| 10. 管理后台查看 | 管理端 `/` 看板；`/posts`等仍占位 | `POST /auth/login`、`GET /admin/dashboard`；按需`GET /admin/users` | `users`、`posts`、`point_records`、`ai_creations` | 成员5；成员1守权限契约 | ✅ 管理登录/看板API和403隔离已验证；🟡页面真实联调待完成 | 管理员种子账号从本地安全配置读取；不得前端硬编码密码 | 管理员看板成功；普通用户403；统计与数据库一致 | 帖子审核页、模板/路线管理占位 | 是：管理员权限、统计响应和审计操作 |

## 公共变更闸门

- **成员2 → 公共依赖**：只消费既有契约；若需要新增详情路由参数、分页字段或错误码，先与对应成员确认，再由角色1审核 API。不要在前端保存AI Key。
- **成员3 → 待审重点**：AI问答新契约、Creation状态机、Provider回调/轮询、对象存储字段；能复用`creation_templates`和`ai_creations`时不新增表。
- **成员4 → 待审重点**：定位/二维码证据、任务校验、徽章自动授予；不得改变`user_task_records(user_id,task_id)`和`point_records(user_id,business_key)`幂等约束。
- **成员5 → 待审重点**：评论/社区页面和最小管理联调可使用现有骨架；举报、排行、活动、复杂审核等不进入当前主流程，新增表或接口必须单独立项。
- **角色1 → 集成职责**：冻结公共API路径、审核迁移与权限、维护统一响应/CORS/部署；不代做成员2–5完整业务。

## 联调通过线

按表中1→10顺序使用同一测试用户和真实MySQL串联；每步记录请求路径、HTTP状态、业务`code`、`requestId`和关键数据ID。失败时停在首个断点，不手工改库跳过。合入前至少提供：前端截图/录屏、接口证据、类型检查或构建结果；涉及公共API/数据库的PR须有角色1审核。
