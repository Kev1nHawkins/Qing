# 五人团队开发说明

## 分支策略

- `main`：最终稳定演示版本，仅项目负责人在里程碑验收后合并。
- `develop`：日常集成分支，所有功能 PR 的目标分支。
- `feature/<issue>-<name>`：新功能。
- `fix/<issue>-<name>`：缺陷修复。
- `docs/<issue>-<name>`：文档或演示数据。

从 `develop` 拉取功能分支，完成后推送并创建 PR：

```bash
git switch develop
git pull --ff-only
git switch -c feature/12-culture-detail
git add .
git commit -m "feat(culture): add culture detail API"
git push -u origin feature/12-culture-detail
```

## Commit 规范

格式：`type(scope): summary`

| type | 用途 |
|---|---|
| `feat` | 新功能 |
| `fix` | 缺陷修复 |
| `docs` | 文档 |
| `refactor` | 不改变行为的重构 |
| `test` | 测试 |
| `chore` | 工具、依赖、构建 |
| `perf` | 性能优化 |
| `ci` | CI/CD |

## 公共文件所有权

- 数据库模型、`alembic/versions`、后端公共配置、Compose：成员 1。
- 用户端公共组件与请求封装：成员 2。
- AI Adapter、Prompt、知识库：成员 3。
- 路线任务、地图、积分徽章：成员 4。
- 社区、管理后台、演示内容：成员 5。

修改不属于自己主责的公共文件时，必须先建 Issue 并通知所有者。数据库迁移只由成员 1 生成。

## 每日节奏

- 10 分钟晨会：昨天完成、今天计划、当前阻塞。
- 阻塞超过 2 小时立即反馈。
- 21:30 前推送个人分支、更新 Issue、提交或更新 PR。
- 22:00 项目负责人拉取 `develop`，执行启动和主流程检查。

## 完成定义

每个功能必须同时具备：

1. 可合并代码，无密钥和个人路径。
2. Swagger 或接口文档更新。
3. 可复现测试步骤。
4. 截图、接口返回或录屏证据。
5. 受影响接口、迁移和已知风险说明。

