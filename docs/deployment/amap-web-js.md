# 高德地图 Web JS API 配置与降级说明

## 1. 配置项

在高德开放平台创建应用并添加 `Web端（JS API）` Key。将真实配置写入项目根目录
`.env`：

```dotenv
VITE_AMAP_KEY=你的Web端JS_API_Key
VITE_AMAP_SECURITY_CODE=你的Web端安全密钥
```

`.env` 已被 `.gitignore` 忽略。仓库中的 `.env.example` 只保留变量名和空值，不得提交
真实 Key 或安全密钥。

高德 Web JS API 配置会进入浏览器端运行环境，因此还应在高德控制台设置允许访问的域名，
并为本地、测试和正式环境分别创建 Key。

## 2. Docker Compose 启动

`docker-compose.yml` 将根目录 `.env` 中的配置透传到 `frontend-user`：

```yaml
VITE_AMAP_KEY: "${VITE_AMAP_KEY:-}"
VITE_AMAP_SECURITY_CODE: "${VITE_AMAP_SECURITY_CODE:-}"
```

配置变更后需要重建或重新创建用户端容器：

```powershell
docker compose up -d --no-deps --force-recreate frontend-user
```

访问 `http://localhost:5173/routes`。地图状态显示“高德地图实时校园路线”且任务标记可见，
表示配置已生效。

## 3. GitHub Actions 或服务器部署

不要上传本地 `.env`。在 GitHub 仓库的
`Settings -> Secrets and variables -> Actions` 中配置：

- `VITE_AMAP_KEY`
- `VITE_AMAP_SECURITY_CODE`

构建用户端时注入：

```yaml
- name: Build user frontend
  working-directory: frontend-user
  env:
    VITE_AMAP_KEY: ${{ secrets.VITE_AMAP_KEY }}
    VITE_AMAP_SECURITY_CODE: ${{ secrets.VITE_AMAP_SECURITY_CODE }}
  run: |
    npm ci
    npm run build
```

如果在服务器上使用 Docker Compose，则直接在服务器项目根目录创建 `.env`，无需把真实值
写入仓库。

## 4. 自动降级行为

用户端在以下场景自动切换为离线校园示意图：

- `VITE_AMAP_KEY` 为空；
- 高德脚本加载失败；
- 高德脚本加载超过 8 秒；
- 脚本已加载但 `AMap` 未正确初始化；
- 创建地图、标记或路线折线时发生异常。

降级后页面仍保留：

- 当前路线和任务时间线；
- 离线校园轮廓和中心湖示意；
- 全部任务标记及标记点击交互；
- 路线领取、任务提交、积分、徽章和商城主流程。

页面会显示具体原因和“已切换为离线校园示意图”，不会因为第三方地图不可用阻断比赛演示。

实现位置：

- `frontend-user/src/views/map/CampusMap.vue`
- `docker-compose.yml`
- `.env.example`

## 5. 验收

在线模式：

1. 配置两个环境变量并重新创建 `frontend-user`。
2. 打开 `/routes`。
3. 确认显示“高德地图实时校园路线”。
4. 切换三条路线，确认地图标记和折线同步更新。

降级模式：

1. 在临时测试环境中将 `VITE_AMAP_KEY` 设为空，或阻断
   `https://webapi.amap.com/maps`。
2. 重新启动用户端并打开 `/routes`。
3. 确认显示离线校园示意图和降级原因。
4. 确认任务标记、任务时间线、积分和商城区域仍可使用。

不要为了测试降级而删除或提交本地 `.env`。
