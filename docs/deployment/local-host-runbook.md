# 宿主机演示运行手册

## 适用范围

本手册用于 Windows 宿主机运行 FastAPI 后端，并复用 Docker Compose 中现有的 MySQL 8.4。当前已实际验证：Python 3.12.13、真实 Uvicorn/TCP、`/health`、Swagger、OpenAPI 32 条路径，以及 17 项核心 HTTP 流程。

## 环境要求

- Windows 10/11 与 PowerShell 5.1 或更高版本
- Python 3.12.x
- Docker Desktop
- 本机端口 3306、8000 可用

不要使用 Python 3.14 创建项目虚拟环境。当前固定依赖已在 Python 3.12 验证，未确认与 Python 3.14 完全兼容。

## 首次准备

在项目根目录执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip check
Copy-Item .env.example .env
```

检查 `.env`，替换 JWT、MySQL 和管理员的开发默认值。不要提交 `.env`。

## MySQL、迁移与种子数据

```powershell
docker compose up -d --no-build --pull never mysql
docker compose ps mysql
docker compose logs --tail 80 mysql
```

必须确认 `lingchao-mysql` 为 `healthy`。宿主机运行后端时，`DATABASE_URL` 的主机应为 `127.0.0.1:3306`；容器内运行时应为 `mysql:3306`。

手动执行迁移和种子：

```powershell
$env:DATABASE_URL = "从本地 .env 读取并将主机设为 127.0.0.1 的连接串"
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m app.scripts.seed
Set-Location ..
```

不要把数据库密码粘贴进共享日志或提交记录。种子脚本已验证可重复执行，但演示前仍应先备份数据。

## 一键启动与停止

```powershell
.\scripts\demo-start-host.ps1
.\scripts\demo-status.ps1
```

启动脚本会检查 Docker Engine、等待 MySQL healthy、检查 `.venv` 和端口 8000，以无 `--reload` 的单进程模式启动 Uvicorn，并将 PID 与日志保存在 `work`。

访问地址：

- Health：<http://127.0.0.1:8000/health>
- Swagger：<http://127.0.0.1:8000/docs>
- OpenAPI：<http://127.0.0.1:8000/openapi.json>

停止后端：

```powershell
.\scripts\demo-stop-host.ps1
```

停止脚本只终止 PID 文件所指向、且命令行匹配本项目路径与 Uvicorn 的进程；不会停止 MySQL 或其他 Python 进程。

## 手工启动备用命令

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

演示模式不要添加 `--reload`。手工启动时由当前终端负责生命周期，按 `Ctrl+C` 停止。

## 前端开发代理

- 用户端：`http://127.0.0.1:5173`
- 管理端：`http://127.0.0.1:5174`
- 浏览器使用相对 API Base URL `/api/v1`
- Vite 将 `/api` 代理到 `http://127.0.0.1:8000`

后端 CORS 默认覆盖上述 localhost 和 127.0.0.1 两组地址。若端口或域名变化，通过 `CORS_ORIGINS` 配置，不要修改 API 源码。
