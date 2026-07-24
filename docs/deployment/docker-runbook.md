# Docker Compose 运行手册

## 当前验证状态

Compose 配置已通过静态校验，MySQL 8.4 容器和原数据卷已实际验证为 healthy。后端镜像构建仍受阻于 Docker Hub 的 `auth.docker.io` 连接失败，因此后端容器、两个前端容器和四服务联调尚未实际通过。

不得把本手册中的静态配置结论描述为容器运行验证。

## 所需镜像

- `mysql:8.4`（本机已存在）
- `python:3.12-slim`（后端基础镜像，当前缺失）
- `node:22-alpine`（两个前端当前开发容器的基础镜像）

不使用未知第三方镜像源。网络恢复后从官方 Docker Hub 获取。

## 构建

```powershell
docker compose config --quiet
docker compose build backend
docker compose build frontend-user
docker compose build frontend-admin
```

本阶段只验证过后端构建命令到基础镜像元数据步骤；由于 Docker Hub认证端点超时，镜像未生成。不要无诊断地重复构建。

## 服务与端口

| 服务 | 容器端口 | 宿主机端口 | 内部依赖 |
|---|---:|---:|---|
| mysql | 3306 | 3306 | — |
| backend | 8000 | 8000 | `mysql:3306` |
| frontend-user | 5173 | 5173 | `backend:8000` |
| frontend-admin | 5174 | 5174 | `backend:8000` |

所有服务连接 Compose 网络 `lingchao`。浏览器不能解析 `backend`；浏览器只请求相对 `/api/v1`，由容器内代理转发。

## 启动顺序

已有全部镜像后执行：

```powershell
.\scripts\demo-start-docker.ps1
```

该脚本实际使用 `docker compose up -d --no-build --pull never`，不会构建或拉取。若镜像不存在会明确失败。

手工分步检查：

```powershell
docker compose up -d --no-build --pull never mysql
docker compose ps mysql
docker compose up -d --no-build --pull never backend
docker compose ps backend
docker compose logs --tail 100 backend
```

backend 入口会依次执行：

1. `alembic upgrade head`
2. `python -m app.scripts.seed`
3. 启动 Uvicorn

迁移和种子策略均设计为可重复执行，但不得手工删除迁移版本或清空数据库来规避错误。

## 健康与HTTP检查

```powershell
docker compose ps
docker compose logs --tail 100 mysql
docker compose logs --tail 100 backend
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/docs -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8000/openapi.json -UseBasicParsing
```

预期：MySQL与backend均 healthy，三个HTTP端点返回200，OpenAPI不少于32条路径。

## 数据卷保护

当前命名卷包括 MySQL 数据卷和上传文件卷。停止演示使用：

```powershell
.\scripts\demo-stop-docker.ps1
```

该脚本只执行 `docker compose stop`。不得执行 `docker compose down -v`、`docker system prune`，也不得删除 MySQL 容器或数据卷。停止后容器、镜像和数据均应保留。

## 前端生产部署缺口

当前两个前端 Dockerfile 运行 Vite 开发服务器，并非 Nginx 生产镜像；项目当前也没有生产 Nginx 配置。因此：

- Compose开发代理：配置已审计一致；
- 生产Nginx反向代理：尚未实现、尚未运行验证；
- 后续应在独立部署变更中增加多阶段构建与 Nginx `/api` 到 `http://backend:8000` 的代理，不应在比赛临场直接替换。
