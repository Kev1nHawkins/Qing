# 冒烟测试

1. 执行 `docker compose up --build`，等待四个服务均为 healthy/running。
2. 打开 `/health`，确认 `code=0` 且包含 `requestId`。
3. 打开 `/docs`，使用 `POST /api/v1/auth/login` 登录。
4. 在 Swagger 的 `Authorize` 中粘贴返回的 JWT。
5. 查询文化、地点、路线与任务列表，确认存在红棉演示数据。
6. 新建普通用户，完成任务 1 两次；第二次返回 `alreadyCompleted=true` 且积分不增加。
7. 发布帖子并连续切换点赞，确认计数不会重复累计或小于 0。
8. 管理员访问 `/api/v1/admin/dashboard`；普通用户访问应返回 403。
9. 重启所有容器，确认迁移和种子脚本可重复执行。

