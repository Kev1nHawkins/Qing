# 岭潮共创：团队从这里开始

## 1. 项目定位

岭潮共创是面向大学生比赛的“岭南文化与校园文化 AI 共创传播平台”，以文化内容、校园寻迹、AI 创作和社区传播串联完整体验。

## 2. 五人分工

| 成员 | 主责 | 首日动作 |
|---|---|---|
| 1 | 项目管理、后端基础架构、迁移、鉴权、部署、API 契约 | 复核基线、建立 Issue/PR 规则、补真实 TCP 与 Compose 验证计划 |
| 2 | 用户端 Vue | 从 `feature/member2-user-frontend` 建分支，核对路由与联调契约 |
| 3 | AI 问答、Prompt、文生图 | 从 `feature/member3-ai-creation` 建分支，先提交 Provider/状态机设计 |
| 4 | 地图、路线任务、积分徽章 | 从 `feature/member4-route-points` 建分支，先验证任务幂等和地图权限方案 |
| 5 | 社区和管理端 | 阅读两份成员 5 文档，从 `feature/member5-admin-community` 建分支 |

## 3. 项目目录

```text
backend/            FastAPI、SQLAlchemy、Alembic、测试
frontend-user/      Vue 用户端
frontend-admin/     Vue 管理端
docs/               API、数据库、需求、测试和交接文档
data/               演示数据、知识库与 Prompt 预留
deploy/             部署说明
scripts/            启停脚本
.github/            Issue/PR 模板与 CODEOWNERS
docker-compose.yml  四服务开发编排
```

## 4. 开发环境

- Python 3.12，MySQL 8.4，Docker Desktop/Compose v2。
- Node.js 24 当前验证通过；前端依赖使用仓库固定的 pnpm 工作区和锁文件。
- 从 `.env.example` 复制本地 `.env` 并更换开发密钥；`.env` 永不提交。
- API 固定 `/api/v1`，响应固定 `{code, message, data, requestId}`。

## 5. 常用命令

后端本机启动（当前环境尚未完成真实 TCP 验证）：

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

数据库迁移与种子：

```powershell
cd backend
alembic upgrade head
python -m app.scripts.seed
```

前端检查与构建：

```powershell
pnpm --dir frontend-user exec vue-tsc --noEmit
pnpm --dir frontend-user run build
pnpm --dir frontend-admin exec vue-tsc --noEmit
pnpm --dir frontend-admin run build
```

Docker 配置静态检查：

```powershell
docker compose config --quiet
```

不要在没有协调的情况下更新锁文件、升级主依赖或清理共享数据库卷。

## 6. 当前验证状态

已验证：真实 MySQL 8.4 的初始迁移和幂等种子；FastAPI TestClient + 真实 MySQL 的 17 项核心业务；两个 Vue 前端类型检查和生产构建。

未验证：Uvicorn 真实 TCP 监听；后端 Docker 容器；四服务 Compose 联调；浏览器真实端到端请求；外部 AI、地图、二维码、对象存储。

## 7. Git 与 PR 规则

- 长期分支：`main`（稳定基线）、`develop`（集成）；开发分支：`feature/*`，修复：`fix/*`，文档：`docs/*`。
- Commit 使用 `feat:`、`fix:`、`docs:`、`chore:`、`test:`、`refactor:`。
- 不直接向 `main` 或 `develop` 推送；从 Issue 建分支，经 PR、检查和责任人 Review 后合并。
- PR 应小而单一，写清变更、验证命令、截图/接口结果、迁移影响和回退方式。
- 数据库变化必须先 Issue，由成员 1 审核并统一生成 Alembic 迁移。

## 8. 公共文件负责人

| 公共区域 | 负责人/审批人 |
|---|---|
| `backend/app/core`、认证、统一响应、`api/router.py` | 成员 1 |
| Models、Alembic、`seed.py` | 成员 1 审批；领域成员提供需求 |
| `frontend-user/src/router`、用户端公共样式/API | 成员 2 |
| Creation/Prompt 契约 | 成员 3，成员 1 审核公共 API |
| Route/Task/Points/Badge 契约 | 成员 4，成员 1 审核迁移/API |
| Community/Admin 领域与管理端路由 | 成员 5；公共认证由成员 1 审核 |
| `docker-compose.yml`、`.env.example`、GitHub 规范 | 成员 1 |

## 9. 冲突处理

发现冲突先停止在共享文件继续堆叠修改，在群内声明文件和目标；由文件负责人确定契约，开发者在自己的 feature 分支同步 `develop` 后局部解决。不得用覆盖整文件的方式消除他人改动。涉及 API/数据库时先补 Issue 和文档，再由成员 1 仲裁；合并后由相关成员共同执行最小回归。

## 10. 接手入口

- 成员 1：`docs/handover/member1-backend-architecture.md`
- 成员 2：`docs/handover/member2-frontend-user.md`
- 成员 3：`docs/handover/member3-ai.md`
- 成员 4：`docs/handover/member4-route-points.md`
- 成员 5：`docs/handover/member5-admin-community.md` 与 `docs/handover/member5-community.md`
