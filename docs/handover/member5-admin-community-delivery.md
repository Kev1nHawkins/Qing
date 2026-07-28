# 成员 5：社区、管理后台与演示内容交付

## 完成内容

- 用户端共创社区：公开信息流、内容类型筛选、AI 作品/文化内容关联、发布、
  点赞、评论、收藏和文化标签。
- 计数一致性：点赞保持既有幂等语义；点赞、评论、收藏均以关系表为事实来源，
  写入时使用唯一约束与原子计数更新。
- 权限：普通用户只能发布自己的成功 AI 作品；内容作者可发布自己的作品；
  管理员可查看审核列表并通过、驳回或下架。
- 管理后台：状态指标、状态筛选、关键词搜索、分页、内容预览抽屉和基础审核。
- 演示内容：20 条固定社区内容、3 个普通用户账号、真实点赞/收藏/评论关系，
  两张已授权实景图片及一张 AI 原创演示插画。
- 安全整理：移除用户端和管理端登录页的默认账号密码。

## 主要文件

- 后端：`backend/app/api/community.py`、`backend/app/api/admin.py`、
  `backend/app/services/community.py`、`backend/app/schemas/community.py`
- 用户端：`frontend-user/src/views/CommunityView.vue`、
  `frontend-user/src/components/Community*.vue`、
  `frontend-user/src/community/community.css`
- 管理端：`frontend-admin/src/views/PostManageView.vue`
- 演示：`backend/app/scripts/seed_community_demo.py`、`data/demo/`
- 设计：`docs/design/member5-community-concept.png`、
  `docs/design/member5-admin-concept.png`
- 测试：`backend/tests/test_community.py`

## API 与数据库

- 新增 `GET /api/v1/admin/posts`。
- `GET /api/v1/community/posts` 新增 `contentType`、`tag` 筛选参数。
- 帖子和评论响应仅新增可选展示字段，原字段未删除或改名。
- 数据库结构：无变更，无 Alembic 迁移。

## 验证结果

- `backend/.venv/Scripts/python.exe -m pytest -q`：4 passed。
- 两个前端 `vue-tsc --noEmit`：通过。
- 两个前端 `pnpm run build`：通过；管理端仅有 Element Plus 既有大包提示。
- 真实 MySQL + HTTP 冒烟：19 passed、0 failed。
- Playwright/Edge：
  - 发布、关联 AI 作品、点赞、重复点赞、收藏、评论通过；
  - 重复点赞后计数保持不变；
  - 管理员搜索、预览、下架通过，并恢复测试内容；
  - 桌面和 390px 手机端无横向溢出，控制台 0 错误。

当前环境没有 Browser 插件，因此浏览器验收按前端测试规范使用本机
Playwright Core + Microsoft Edge。

## 本地演示初始化

```powershell
cd backend
python -m app.scripts.seed
$env:LINGCHAO_DEMO_PASSWORD = "在本机设置至少8位的演示密码"
python -m app.scripts.seed_community_demo
```

脚本幂等。演示账号名见 `data/demo/README.md`，密码不写入仓库。

## 留待成员 1 / 后续迭代

- 举报、官方活动配置和完整审核操作日志需要新增表或字段，按协作约定先由成员 1
  审核并生成迁移，本交付未越权修改数据库。
- 当前后台是比赛演示所需的基础审核 CRUD，不包含复杂运营规则或批量审核。
- 帖子封面使用 URL 或演示静态资源；正式文件上传与对象存储不在本成员范围。
