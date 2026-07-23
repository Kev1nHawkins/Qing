# 成员 1：后端基础架构交接

## 1. 职责边界

成员 1 是项目负责人和后端基础架构负责人，后续只负责工程稳定性、数据库迁移、登录与权限、文化内容基础 API、Docker/部署、API 契约、协作规范和各模块公共骨架。不得继续代做成员 2 的完整用户端、成员 3 的 AI 能力、成员 4 的地图与游戏化、成员 5 的社区与运营后台。

## 2. 技术栈与目录

- Python 3.12、FastAPI、Pydantic v2。
- SQLAlchemy 2.0 异步 ORM、asyncmy、MySQL 8.4、Alembic。
- JWT Bearer 登录，密码哈希由 `app/core/security.py` 负责。
- structlog 统一日志；中间件生成 `requestId`；全局异常处理统一响应。
- Swagger `/docs`、ReDoc `/redoc`、OpenAPI `/openapi.json`。

主要目录：

```text
backend/
├─ alembic/                 # 迁移环境和版本文件
├─ app/api/                 # 10 个 APIRouter 模块及公共依赖
├─ app/core/                # 配置、数据库、JWT、日志、异常、中间件、响应
├─ app/models/              # SQLAlchemy 2.0 模型
├─ app/schemas/             # Pydantic 请求/响应模型
├─ app/services/            # 公共领域服务，目前含积分服务
├─ app/scripts/seed.py      # 幂等种子数据
├─ tests/smoke_real_mysql.py
├─ alembic.ini
├─ Dockerfile
└─ requirements.txt
```

## 3. 数据库与 Alembic

在 `backend` 目录、激活虚拟环境并配置真实 `DATABASE_URL` 后执行：

```powershell
alembic current
alembic upgrade head
python -m app.scripts.seed
```

初始迁移是 `backend/alembic/versions/20260723_0001_initial_schema.py`。任何结构变更必须先建 Issue，经成员 1 审核，再由成员 1 统一生成和复核 Alembic 迁移；禁止成员自行改字段、改外键或只改 Model 不交迁移。

## 4. 认证、权限与公共基础设施

- 登录接口签发 JWT；受保护接口通过 `CurrentUser` 解析用户。
- 管理接口通过 `AdminUser` 验证 `role.code == "admin"`，普通用户应得到 HTTP 403。
- `app/core/exceptions.py` 处理业务和框架异常。
- `app/core/logging.py` 与 `app/core/middleware.py` 提供结构化日志和请求 ID。
- 所有业务 API 使用 `/api/v1` 前缀，响应固定为 `{code, message, data, requestId}`。
- `.env` 不提交；生产环境必须替换开发用 JWT 和管理员占位值。

## 5. 19 张数据表

| 领域 | 表 |
|---|---|
| 用户与文件 | `roles`、`users`、`file_assets` |
| 文化与地点 | `culture_items`、`locations` |
| 路线任务 | `routes`、`route_tasks`、`user_task_records` |
| AI 创作 | `creation_templates`、`ai_creations` |
| 社区 | `posts`、`comments`、`post_likes`、`favorites`、`tags`、`post_tags` |
| 积分徽章 | `point_records`、`badges`、`user_badges` |

ER 关系详见 `docs/database/er-diagram.md`。

## 6. 10 个 APIRouter 模块

| 模块 | 前缀 | 范围 |
|---|---|---|
| Auth | `/api/v1/auth` | 注册、登录、当前用户 |
| Culture | `/api/v1/cultures` | 文化条目基础 CRUD |
| Location | `/api/v1/locations` | 校园地点基础 CRUD |
| Route | `/api/v1/routes` | 路线列表、详情、开始、管理 CRUD |
| Task | `/api/v1/tasks` | 任务 CRUD 与完成任务 |
| Creation | `/api/v1/creations` | 模板、作品任务基础骨架 |
| Community | `/api/v1/community` | 帖子、评论、点赞等基础骨架 |
| Points | `/api/v1/points` | 积分概览和流水 |
| Badge | `/api/v1/badges` | 徽章列表、我的徽章、管理创建 |
| Admin | `/api/v1/admin` | 看板、用户、帖子审核、积分调整骨架 |

## 7. 已验证的 17 项核心业务

以下项目已通过 FastAPI TestClient 连接真实 MySQL 8.4 实际验证：健康检查、用户注册、用户登录、当前用户、文化列表、文化详情、路线列表、路线详情、开始路线、完成任务、积分流水、重复完成任务不重复加分、创建社区帖子、点赞帖子、重复点赞不重复计数、普通用户访问管理接口被拒绝、管理员访问管理接口成功。

这验证了路由、鉴权、真实数据库读写、权限隔离和关键幂等逻辑，但不等同于真实 TCP 网络验证。

## 8. 当前未验证项

- Uvicorn 在宿主机 `127.0.0.1:8000` 的真实 TCP 监听。
- 后端 Docker 镜像构建与容器启动。
- MySQL、后端、用户端、管理端四服务 Compose 联调。
- 浏览器端到后端的真实跨服务请求、生产代理与 CORS。
- 外部 AI 服务、地图 SDK、真实定位、真实二维码和对象存储。

## 9. 变更规则

数据库字段、外键、索引、枚举变更必须先 Issue、成员 1 审核、迁移与 Model 同 PR，并提供升级/回退说明。API 路径和统一响应不得私自改变；新增字段优先保持向后兼容，涉及公共契约时先更新 `docs/api` 和 OpenAPI 验收说明。

## 10. 后续工作边界

成员 1 可继续处理：迁移审查、认证授权缺陷、公共异常/日志/响应、文化基础 API、Docker 和部署、Swagger 契约、CI 与协作规范。禁止继续实现完整 AI 生成、地图打卡/玩法、社区收藏/排行/举报/活动/审核流程或对应前端页面。
