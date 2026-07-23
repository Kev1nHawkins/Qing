# 岭潮共创：GitHub 团队接入指南

## 1. 当前远程准备状态

本文件生成时，本机未安装 GitHub CLI，仓库也没有 `origin`，因此远程仓库、线上分支和保护规则均尚未创建。由成员 1 完成私有仓库创建后，将 `<GITHUB_OWNER>` 替换为实际组织或用户名。

若手动安装并登录 GitHub CLI，可由成员 1 在 D 盘正式仓库执行：

```powershell
gh auth status
gh repo create lingchao-co-create --private --source . --remote origin
git push -u origin main
git push -u origin develop
```

禁止使用 `--force`。创建前必须确认同名仓库不存在；若存在，停止并核对归属和权限。

也可以在 GitHub 网页新建空的 private 仓库（不要初始化 README、`.gitignore` 或 License），然后执行：

```powershell
git remote add origin https://github.com/<GITHUB_OWNER>/lingchao-co-create.git
git push -u origin main
git push -u origin develop
```

## 2. 克隆与进入 develop

```powershell
git clone https://github.com/<GITHUB_OWNER>/lingchao-co-create.git
cd lingchao-co-create
git switch develop
git pull --ff-only origin develop
```

第一次运行前阅读 `AGENTS.md`、`docs/handover/team-start-here.md` 和自己的交接文档。`.env.example` 只能复制为本地 `.env`，真实 `.env` 不提交。

## 3. 每个成员的第一条分支命令

在已切换并更新 `develop` 后，每人只执行自己的命令：

```powershell
# 成员 1
git switch -c fix/member1-deployment

# 成员 2
git switch -c feature/member2-user-frontend

# 成员 3
git switch -c feature/member3-ai-creation

# 成员 4
git switch -c feature/member4-route-points

# 成员 5
git switch -c feature/member5-admin-community
```

一条分支只完成一个 Issue。不得直接在 `main` 或 `develop` 工作。

## 4. 提交与 push

提交前先检查差异和敏感文件：

```powershell
git status
git diff
git add <明确文件路径>
git diff --cached
git commit -m "feat: concise change description"
git push -u origin <当前feature分支>
```

Commit 前缀使用 `feat`、`fix`、`docs`、`test`、`refactor`、`chore`。禁止提交 `.env`、Token、API Key、数据库密码、日志、虚拟环境、`node_modules` 或 `dist`。

## 5. Pull Request 流程

1. PR 的 base 选择 `develop`，compare 选择个人 feature/fix 分支。
2. 标题遵循 Commit 规范，例如 `feat: add route progress UI`。
3. 关联 Issue，列出范围、不做内容、风险和回退方式。
4. 标记潜在冲突文件和是否涉及 API、数据库、锁文件。
5. 等待 CI 通过和至少一名责任人 Review；不得自行合并未通过检查的 PR。
6. `develop` 稳定后由成员 1 发起面向 `main` 的发布 PR。

## 6. PR 测试证据

每个 PR 至少提供与改动相称的证据：

- 执行过的命令、退出码和关键日志。
- 前端变更提供截图/录屏、类型检查和生产构建结果。
- 后端变更提供 HTTP 状态、`code/message`、关键 `data` 和 Swagger 变化。
- 幂等、权限或异常修改必须包含重复请求、普通用户/管理员和失败用例。
- 数据库变更必须包含 Issue、迁移文件、升级/回退说明及成员 1 Review。
- 未执行的测试必须写“未验证”，不得描述为通过。

## 7. 每日同步 develop

```powershell
git switch develop
git pull --ff-only origin develop
git switch <个人分支>
git merge develop
```

团队默认使用 merge 同步，避免多人阶段随意 rebase/force push。若确需 rebase，必须由分支唯一负责人确认且不能改写共享分支历史。

## 8. 冲突处理

1. 停止继续编辑冲突文件，在群内说明文件、分支和目标。
2. 查阅 `team-start-here.md` 的公共文件负责人。
3. 先同步 `develop`，逐段解决，禁止整文件覆盖他人改动。
4. API/数据库冲突由成员 1 仲裁；前端公共路由分别由成员 2/5 协调。
5. 解决后重新执行相关检查，并在 PR 写明冲突解决和回归证据。

## 9. 公共配置修改规则

- `package.json`、`pnpm-lock.yaml`、`pnpm-workspace.yaml`、tsconfig 和 Vite 配置只为明确 Issue 修改，不顺带升级主依赖。
- 修改依赖必须说明原因、锁文件差异、两个前端影响和回退方式。
- `docker-compose.yml`、`.env.example`、后端 core、统一响应和 API router 由成员 1 Review。
- API 固定 `/api/v1`，响应固定 `{code, message, data, requestId}`。
- 数据库变更先建 Issue，由成员 1 审核并统一生成 Alembic 迁移。

## 10. 密钥安全

- 真实密钥只进入本地 `.env`、GitHub Actions Secrets 或批准的密钥管理系统。
- 前端不得保存或直接调用需要秘密 Key 的 AI 服务。
- 日志、Issue、PR、截图和测试证据必须脱敏 Authorization、Cookie、密码和 Token。
- 若误提交密钥，立即停止传播，通知成员 1 吊销/轮换；不能只通过删除最新提交解决。

## 11. 分支保护手动设置

当前尚未在线配置。远程创建后，仓库管理员进入：

`Repository → Settings → Rules → Rulesets → New branch ruleset`

若账号显示旧界面，则进入：

`Repository → Settings → Branches → Add branch protection rule`

`main` 规则：匹配 `main`；要求 Pull Request；至少 1 个 Review；要求 `Backend checks / backend-static` 和 `Frontend checks / frontend-build` 通过；禁止 force push；禁止删除；限制直接更新。

`develop` 规则：匹配 `develop`；要求 Pull Request 和上述 CI；禁止 force push；建议至少 1 个 Review；禁止删除。

只有 Actions 首次实际运行并产生检查名称后，才能在 Required status checks 中选择它们。设置完成后用普通成员账号验证直接 push 被拒绝；未验证前不得声称保护已生效。

## 12. 日常最小检查

```powershell
git status
git branch --show-current
git log -1 --oneline
```

后端静态检查和前端检查以 `.github/workflows/` 为准。CI 不启动 MySQL，也不替代真实 MySQL、TCP、Docker 和浏览器端到端验收。
