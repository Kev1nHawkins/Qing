# 部署扩展

开发环境由根目录 `docker-compose.yml` 管理。生产部署时至少需要：

- 更换 JWT、管理员和数据库密码。
- 移除源码热加载卷和 `--reload`。
- 使用反向代理终止 TLS。
- 将上传目录切换为 MinIO 或 OSS。
- 限制 MySQL 端口不对公网开放。

