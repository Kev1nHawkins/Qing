# 演示数据

基础角色、管理员、徽章、红棉路线和任务由后端基础种子脚本生成。成员 5
另提供 30 条文化内容、40 条社区演示内容、3 个普通用户演示账号和与真实关系
一致的点赞/评论/收藏数据。

```powershell
cd backend
python -m app.scripts.seed
$env:LINGCHAO_DEMO_PASSWORD = "在本机设置至少8位的演示密码"
python -m app.scripts.seed_community_demo
```

脚本幂等，可重复运行；演示密码只从本机环境变量读取，不写入仓库。普通用户账号：

- `lingchao_demo_1`（红棉记录员）
- `lingchao_demo_2`（校园寻迹者）
- `lingchao_demo_3`（岭潮设计社）

管理员用户名由后端本地配置提供。比赛演示前由负责人统一分发本机密码，不在
README、前端默认值、截图或提交记录中保存。

内容源文件：`community-posts.json`。文化图片来源与许可见
`cultural-materials.md`。离线演示图片分别放在两个前端的
`public/demo/` 目录，避免比赛现场依赖外网。

