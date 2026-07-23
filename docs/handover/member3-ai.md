# 成员 3：AI 创作能力交接

## 1. 当前预留位置

- 数据与 Prompt：`data/prompts/`、`data/knowledge_base/`。
- 后端模型：`backend/app/models/creation.py`。
- Schema：`backend/app/schemas/creation.py`。
- API：`backend/app/api/creation.py`。
- 用户端后续入口由成员 2 维护；管理端 `/templates` 当前为占位页。

本交接只描述骨架，不代表 AI 服务已实现。

## 2. Creation 模型与现有 API

`creation_templates` 保存模板名称、唯一 code、描述、`prompt_template`、JSON `options_schema`、预览图、发布状态和可选文化条目关联。`ai_creations` 保存用户、模板、文化条目、标题、最终 prompt、输入 JSON、输出地址、描述、状态、错误和重试次数。

现有路径：

- `GET /api/v1/creations/templates`
- `POST /api/v1/creations/templates`（管理员）
- `PUT /api/v1/creations/templates/{template_id}`（管理员）
- `POST /api/v1/creations`（提交骨架，HTTP 202）
- `GET /api/v1/creations`（当前用户作品）
- `GET /api/v1/creations/{creation_id}`
- `POST /api/v1/creations/{creation_id}/retry`

当前提交接口只按 Python `str.format` 编排模板并写入 `PENDING` 记录，尚未调用外部模型或执行异步任务。

## 3. Prompt 数据结构与状态

`prompt_template` 使用命名占位符，例如 `{culture_element}`、`{campus_landmark}`、`{style}`；`options_schema` 是可选项定义，提交请求的 `options` 是实际值。缺少模板要求字段时当前返回 HTTP 422。

生成状态枚举：`PENDING`、`PROCESSING`、`SUCCESS`、`FAILED`。发布状态共用 `DRAFT`、`PUBLISHED`、`OFFLINE`。

## 4. 建议实现任务

1. 文化问答：基于权威文化资料给出可追溯回答，定义来源字段和拒答策略。
2. Prompt 编排：校验 `options_schema`、版本化模板、避免用户输入突破系统约束。
3. 文生图：实现可替换 Provider、超时/重试、结果落存储及状态更新。
4. 异步处理：将 `PENDING` 任务推进到 `PROCESSING/SUCCESS/FAILED`，保证幂等。
5. 为成员 2 提供模板列表、提交、状态轮询、失败重试和文化问答接口说明。

不得在本分支顺带开发用户端完整页面或修改公共认证、数据库公共基类。

## 5. 不得修改的公共契约

- `/api/v1` 前缀和 `{code, message, data, requestId}` 响应。
- 现有 Creation 路径、JWT/管理员依赖、模型现有字段含义。
- 如确需数据库变更，先建 Issue，由成员 1 审核并统一生成迁移。

## 6. API Key 安全

- Key 只能来自后端运行环境或密钥管理系统，不进入代码、前端、Prompt 数据、日志、截图和 Git。
- `.env` 必须保持忽略，仅提交无真实值的 `.env.example`。
- 日志不得记录 Authorization、完整 Prompt 中的敏感输入或 Provider Key。
- Provider 调用应设置超时、限流和失败降级，测试使用假的测试凭据或 Mock。

## 7. 分支和验收

推荐分支：`feature/member3-ai-creation`。

验收标准：模板参数校验明确；状态机可追踪且重试幂等；至少一个 Provider 通过受控集成测试；失败不会泄露 Key；文化问答带来源或明确无法回答；Swagger 契约保持一致；向成员 2 提供可运行的请求示例；迁移变更已经成员 1 审核。
