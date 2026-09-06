# 演示环境故障排查

排查时先运行：

```powershell
.\scripts\demo-status.ps1
docker compose ps -a
```

不要在未定位原因时删除容器、镜像、卷或重置 Docker Desktop。

## 8000端口占用

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
Get-CimInstance Win32_Process -Filter "ProcessId=<OwningProcess>"
```

只停止能确认属于本项目的 PID。优先使用 `scripts\demo-stop-host.ps1`，不要批量终止 Python。

## ERR_CONNECTION_REFUSED

表示当前端口没有服务监听，常见于 Uvicorn 已按验收要求停止。先运行状态脚本，再启动宿主机后端。不要把连接拒绝误判为 API 业务错误。

## `/docs` 与根路径

项目没有要求根路径 `/` 返回页面。后端入口是：

- `/health`
- `/docs`
- `/openapi.json`
- `/api/v1/...`

访问根路径得到404不代表 Swagger 或 API 服务失败。

## Docker Engine pipe不存在

若出现 Windows named pipe、daemon或Engine不可访问错误：

1. 检查 Docker Desktop 是否正在运行；
2. 正常启动 Docker Desktop并等待Engine就绪；
3. 执行 `docker version` 和 `docker info`。

不要 factory reset、重装或修改系统代理来规避问题。

## MySQL不healthy

```powershell
docker compose ps mysql
docker compose logs --tail 80 mysql
Test-NetConnection 127.0.0.1 -Port 3306
```

保留原数据卷。检查端口冲突、密码变量与磁盘空间，不要删除卷重建。

## DATABASE_URL主机名差异

- 宿主机 Uvicorn：`127.0.0.1:3306`
- Compose backend：`mysql:3306`

宿主机无法解析 Compose 服务名 `mysql`；backend容器内的 `127.0.0.1` 又指向容器自身。脚本会在当前进程中规范宿主机地址，不修改系统环境。

## CORS错误

浏览器控制台若出现 CORS，确认实际 Origin 是否在 `CORS_ORIGINS`：

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:5174`
- `http://127.0.0.1:5174`

Origin包含协议、主机和端口，必须精确匹配。项目允许credentials，因此不能把允许源改成通配符。

## Vite代理错误

宿主机开发默认代理目标为 `http://127.0.0.1:8000`；Compose内通过 `VITE_PROXY_TARGET=http://backend:8000` 覆盖。浏览器源码的 API Base URL 应保持 `/api/v1`，不要写 `http://backend:8000`。

## HTTP客户端代理导致502

曾出现 PowerShell请求 localhost 成功、HTTPX却返回502。诊断时仅检查代理变量是否存在，不输出凭据。独立测试客户端可明确使用：

```python
httpx.Client(base_url="http://127.0.0.1:8000", trust_env=False, timeout=10.0)
```

不要修改系统级代理。浏览器和应用生产流量是否应绕过代理需由部署环境单独确认。

## Docker Hub认证连接失败

已观察到 `auth.docker.io/token` 连接超时，导致 `python:3.12-slim` 无法获取。此时：

1. 保留完整错误；
2. 检查本机是否已有官方基础镜像；
3. 不切换未知镜像源；
4. 网络恢复后再执行一次目标构建。

## Alembic失败

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic current
..\.venv\Scripts\python.exe -m alembic heads
..\.venv\Scripts\python.exe -m alembic upgrade head
```

核对目标数据库后再操作。不要删除 `alembic_version`、回滚生产数据或生成临时迁移来掩盖错误。数据库结构变更必须由角色1审核。

## 日志

- 宿主机演示：`work\demo-host-*.out.log`、`work\demo-host-*.err.log`
- backend容器：`docker compose logs --tail 100 backend`
- MySQL：`docker compose logs --tail 80 mysql`

日志、Token、密码和 `.env` 不得提交。
