# 岭潮共创

岭南文化与校园文化 AI 共创传播平台。比赛版围绕“文化探索 → 校园寻迹 → AI 共创 → 社区发布 → 积分徽章”形成单体闭环，使用 FastAPI、Vue 3、MySQL 8 和 Docker Compose。

## 一键启动

前置条件：Docker Desktop 已启动，可用内存建议不少于 4 GB。

```powershell
Copy-Item .env.example .env
.\scripts\start.ps1
```

macOS/Linux：

```bash
cp .env.example .env
chmod +x scripts/*.sh
./scripts/start.sh
```

也可以直接执行：

```bash
docker compose up --build
```

首次启动会自动创建数据库表、执行 Alembic 迁移并写入演示数据。默认开发账号为 `admin / Admin123!`，仅限本地开发，部署前必须修改 `.env` 中的管理员密码和 JWT 密钥。

| 服务 | 地址 |
|---|---|
| 用户端 H5 | http://localhost:5173 |
| 管理后台 | http://localhost:5174 |
| Swagger | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| 健康检查 | http://localhost:8000/health |
| MySQL | localhost:3306 |

## 目录

```text
lingchao-co-create/
├─ backend/             FastAPI、SQLAlchemy 2.0、Alembic
├─ frontend-user/       Vue 3 移动端 H5
├─ frontend-admin/      Vue 3 + Element Plus 管理端
├─ data/                知识库、Prompt、演示数据
├─ docs/                API、数据库、需求和测试文档
├─ deploy/              部署扩展配置
├─ scripts/             启停与开发脚本
├─ .github/             Issue、PR、CODEOWNERS
├─ docker-compose.yml
└─ .env.example
```

## 后端开发

业务模块位于 `backend/app/api`，路由统一由 `router.py` 注册。任何新接口必须：

1. 保持 `/api/v1` 前缀和现有资源路径。
2. 使用 Pydantic 请求模型，不直接接收任意字典。
3. 返回 `{code, message, data, requestId}`。
4. 写操作显式校验当前用户或管理员权限。
5. 涉及积分、点赞、打卡时保证数据库级幂等。

新增迁移：

```bash
docker compose exec backend alembic revision --autogenerate -m "describe_change"
docker compose exec backend alembic upgrade head
```

数据库字段不得由成员自行修改。先创建 Issue，说明字段、默认值、兼容方案和受影响接口，由角色 1 统一生成迁移。

## 前端开发

两个前端通过 Vite 代理访问 `backend:8000`，接口基地址为 `/api/v1`。用户端端口 5173，管理端端口 5174。JWT 分别保存在开发环境的浏览器存储中；正式部署建议改为安全 Cookie 或加强 XSS 防护。

## 常用命令

```bash
docker compose up --build
docker compose logs -f backend
docker compose exec backend pytest
docker compose exec backend alembic current
docker compose down
docker compose down -v  # 会删除本地开发数据库，请谨慎
```

## 协作底线

- `main` 仅保存稳定演示版本；日常 PR 合入 `develop`。
- 分支使用 `feature/*`、`fix/*`、`docs/*`。
- 提交使用 `feat`、`fix`、`docs`、`refactor`、`test`、`chore` 等类型。
- 不提交 `.env`、API Key、密码、个人数据或未授权素材。
- 每个功能交付代码、接口/README、测试步骤和截图/录屏证据。

完整流程见 `docs/team-development.md`，数据关系见 `docs/database/er-diagram.md`。

