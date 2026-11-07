# 软件设计说明（SDD）：Pet-Agent S1.5

- 版本：1.0
- 日期：2026-11-07
- 范围：`backend-agent/`（Agent 运行时）+ `pet-lumina-app` 聊天页（消费方）
- 关联：[总体方案](pet-agent-architecture.md) · [运行时 SPEC](../spec/agent-runtime-api.md) · [Web SPEC](../spec/web-chat-ui.md)

## 1. 上下文

```mermaid
flowchart LR
  U[App 用户] -->|HTTPS + satoken| APP[pet-lumina-app]
  APP -->|SSE /agent/chat| RT[backend-agent<br/>FastAPI + LangGraph]
  APP -->|JSON /api/v1| JAVA[Spring Boot]
  RT -->|JSON /api/v1 + satoken| JAVA
  RT -->|chat completions| LLM[(LLM 服务)]
  RT -->|会话/消息/运行/审计| DB[(MySQL 5 张表)]
  RT -->|短期事件缓冲| MEM[(进程内 RunEventLog)]
  ADMIN[管理端 pet-lumina-web] -.->|S4 规划：工作台| RT
```

两条硬边界：

1. **业务真源在 Java**。Agent 不拥有宠物、健康、记录数据，只读不写（写操作当前只回 proposal，见 ADR-0002）。
2. **身份只有一个来源**。Java 发的 `satoken` 透传，Runtime 拿它换 `user_id`；前端不能自报用户。

## 2. 运行单元

| 单元 | 技术 | 端口（dev） | 职责 |
| --- | --- | --- | --- |
| `pet-lumina-app` | Vue 3.5 + Vite 6 | 5173 | 对话 UI、SSE 消费、会话持久化 |
| `backend-agent` | FastAPI + LangGraph 1.2.20 + aiomysql | 8099 | 路由、图执行、工具网关、事件流、落库 |
| Spring Boot | 2.7.18 + SaToken | 8080 | 业务数据 + 鉴权（Agent 的唯一数据源） |
| `tests/stub_java.py` | FastAPI | 8097 | 本地无 JDK 时的契约桩 |
| `tests/stub_llm.py` | FastAPI | 8098 | 无密钥时的确定性模型桩 |

## 3. 分层与依赖规则

依赖方向**单向**，箭头即 import 方向，反向 import 视为缺陷：

```
api → runtime → graph → tools / storage / llm → domain
```

| 层 | 文件 | 只允许依赖 | 被谁调用 | 关键约束 |
| --- | --- | --- | --- | --- |
| `domain` | `domain/{models,events,router}.py` | 标准库 + pydantic | 所有人 | 纯数据/纯函数；**不 import 任何上层**；路由分类不吃模型 |
| `llm` | `llm/{base,openai_compat,fake}.py` | domain | graph / runtime | 只暴露 `ChatModel` 协议；重试与 usage 归一化在这层 |
| `tools` | `tools/{spec,registry,gateway,client,pet}.py` | domain | graph | schema 由 pydantic 生成；网关是唯一执行入口 |
| `storage` | `storage/{base,memory,mysql}.py` | domain | runtime / api | 一份协议两种实现，契约测试共用 |
| `graph` | `graph/{state,nodes,builder}.py` | domain, llm, tools | runtime | 只描述"怎么想"，不碰网络/存储/日志 |
| `runtime` | `runtime/{runner,eventlog}.py` | graph, storage, domain | api | 编排：建会话→落用户消息→跑图→流式→落助手消息→收尾 run |
| `api` | `api/{deps,schemas,routes,app}.py` | runtime, storage, domain | HTTP | 只做协议转换与鉴权，不放业务逻辑 |

**为什么这么切**：`graph` 里换掉 LangGraph 不影响 `api`；`storage` 换 MySQL 不影响 `graph`；`llm` 换供应商不影响任何业务代码。分层不是为了好看，是为了**改一处不连带三处**。

## 4. 关键流程

### 4.1 L1 直答（约 90% 流量）

```mermaid
sequenceDiagram
  participant C as App
  participant A as api/routes
  participant R as runtime/runner
  participant G as graph
  participant M as llm
  C->>A: POST /agent/chat
  A->>A: 校验 token → user_id
  A->>R: stream(ChatCommand, Caller)
  R->>R: get_or_create_session / add_message(user)
  R->>G: route → prepare → END
  R-->>C: event: route
  R->>M: stream(answer_messages)
  M-->>R: 增量 token
  R-->>C: event: delta × N
  R->>R: add_message(assistant) + finish_run
  R-->>C: event: done
```

要点：**先出 `route` 再出 `delta`**，首字延迟不被工具拖死；`done` 里带完整 `answer` 供前端校正流式拼接。

### 4.2 L2 ReAct（≤ `max_tool_hops` 跳）

图：`START → route → prepare → agent ⇄ tools → END`

1. `prepare` 把 `history + 本轮问题` 写进 `messages`（**L2 必经**，见下方缺陷记录）；
2. `agent` 调模型，模型要么回文本，要么回 `tool_calls`；
3. `tools` 经网关执行（白名单 → 通道 → 预算 → 参数校验 → 副作用判定 → 审计）；
4. 回到 `agent`，直到模型不再要工具或达到 hop 上限；
5. `runner` 用最终上下文做**一次流式生成**，边生成边推 `delta`。

> 缺陷记录：S1 最初 `route → agent` 跳过 `prepare`，模型第一次调用拿到空 `messages`，一个工具都不会调；脚本模型的单测全绿，只有真 SSE 暴露。现在 `route → prepare` 是必经边，并加了回归断言（`tests/test_graph_l2.py`）。

## 5. 数据模型（`backend/sql/v2.10-agent.sql`）

| 表 | 关键列 | 不变量 |
| --- | --- | --- |
| `agent_session` | `id`, `user_id`, `pet_id`, `title`, `message_count`, `status` | 会话有主；`user_id` 只能来自 token |
| `agent_message` | `id`, `session_id`, `role`, `content`, `citations_json`, `run_id` | 只存 `user`/`assistant`；正序 |
| `agent_run` | `id`, `session_id`, `status`, `route`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `error_code` | 必须落到终态（succeeded/failed/cancelled） |
| `agent_step` | `id`, `run_id`, `seq`, `kind`, `name`, `status`, `latency_ms`, `error` | `(run_id, seq)` 连续 |
| `tool_call_log` | `id`, `run_id`, `tool_name`, `args_digest`, `ok`, `error_code`, `latency_ms` | 只存 sha256 前 16 位摘要，不存原文 |

ID：19 位雪花（毫秒 13 + 节点 2 + 序号 4），对外一律字符串，对齐 Java 的 `Long → String` 序列化。

## 6. 错误模型

`AgentError(message, code, http_status, retryable, detail)` 为基类，子类固定语义：

| 类 | code | HTTP | 可重试 | 典型场景 |
| --- | --- | --- | --- | --- |
| `Unauthorized` | `unauthorized` | 401 | 否 | token 缺失/失效 |
| `Forbidden` | `forbidden` | 403 | 否 | 他人会话、通道未开放 |
| `NotFound` | `not_found` | 404 | 否 | 会话/运行不存在（**越权也回 404**，不泄露存在性） |
| `InvalidRequest` | `invalid_request` | 400 | 否 | 空消息、字段非法 |
| `InvalidArguments` | `invalid_arguments` | 400 | 否 | 工具参数校验失败 |
| `ToolDenied` | `tool_denied` | 403 | 否 | 白名单/通道禁用 |
| `BudgetExceeded` | `budget_exceeded` | 429 | 否 | 单 run 工具调用超预算 |
| `ModelNotConfigured` | `model_not_configured` | 503 | 否 | 未配密钥 |
| `ModelError` | `model_error` | 502 | 是 | 上游 5xx/超时 |
| `RunTimeout` | `run_timeout` | 504 | 是 | 超过 `run_deadline_s` |
| `internal_error` | `internal_error` | 500 | 否 | 未预期异常（不暴露堆栈） |

SSE 里错误以 `event: error` 出现，载荷 `{code, message, retryable, detail?}`；`run` 同时落 failed。

## 7. 配置（`PET_AGENT_*`）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `PET_AGENT_ENV` | `dev` | `prod` 下禁用 header 身份模式且强制密钥 |
| `PET_AGENT_AUTH_MODE` | `backend` | `backend`=调 Java 换身份；`header`=仅 dev |
| `PET_AGENT_BACKEND_BASE_URL` | `http://localhost:8080/api/v1` | Java 基址 |
| `PET_AGENT_REPO_BACKEND` | `memory` | `memory` / `mysql` |
| `PET_AGENT_MYSQL_DSN` | 空 | `mysql://user:pwd@host:port/db` |
| `PET_AGENT_LLM_MODEL` | `deepseek-chat` | 模型名 |
| `PET_AGENT_MAX_TOOL_HOPS` | `6` | 图内跳数上限 |
| `PET_AGENT_MAX_TOOL_CALLS_PER_RUN` | `8` | 网关预算 |
| `PET_AGENT_HISTORY_LIMIT` | `20` | 回放进 prompt 的消息条数 |
| `PET_AGENT_RUN_DEADLINE_S` | 见 `config.py` | 单 run 超时 |
| `PET_AGENT_ALLOWED_CHANNELS` | `app,web,internal` | 通道白名单 |
| `PET_AGENT_CORS_ORIGINS` | dev 放开 | 生产必须收敛 |

## 8. 部署（dev）

```powershell
# 1) Java 契约桩（无 JDK 时）
cd backend-agent; .\.venv\Scripts\python -m uvicorn tests.stub_java:app --port 8097
# 2) 模型桩
.\.venv\Scripts\python -m uvicorn tests.stub_llm:app --port 8098
# 3) Runtime
$env:PET_AGENT_LLM_BASE_URL='http://127.0.0.1:8098/v1'; $env:PET_AGENT_LLM_API_KEY='stub'
.\.venv\Scripts\python -m uvicorn app.main:app --port 8099
# 4) App
cd ..\pet-lumina-app; npm run dev
```

生产形态（S2 之后）：`backend-agent` 多副本 + 共享 Redis 事件缓冲 + MySQL；SSE 前面放支持 `X-Accel-Buffering: no` 的网关。

### 8.1 容器与探针（S1.6 P0）

| 项 | 约定 |
| --- | --- |
| 镜像 | `backend-agent/Dockerfile` 多阶段构建（builder 装依赖，runtime 只带 venv + `app/`） |
| 用户 | 非 root：`appuser`，`USER appuser` |
| 端口 | 8099，`uvicorn ... --proxy-headers --forwarded-allow-ips=*` |
| Liveness | `HEALTHCHECK` 打 `GET /healthz`（不查外部依赖） |
| Readiness | 编排系统调 `GET /readyz`：存储不可用 / 模型未配置 → 503 |
| 依赖 | `requirements.txt` 精确版本；`requirements.in` 记人类意图；`requirements-dev.txt` 带 ruff/pytest |
| CI | `.github/workflows/agent-ci.yml`：ruff → pytest → evals → docker build（失败即红） |

### 8.2 可观测（S1.6 P0）

| 项 | 约定 |
| --- | --- |
| 日志 | 单行 JSON（`app/core/logging.py`），必含 `ts/level/logger/msg` |
| 关联字段 | `request_id`（中间件生成/透传）、`user_id`、`run_id`（contextvars 自动附加） |
| 打点位置 | HTTP 访问、run 开始/结束/失败、工具调用（含 `args_digest` 与耗时）、就绪检查 |
| 不记录 | 消息原文、回答原文、工具参数原文、密钥（`repr=False`） |

## 9. 质量属性

| 属性 | 设计手段 | 验收 |
| --- | --- | --- |
| 首字快 | route 确定性分类，先发 `route` 再流式 | e2e 记录 `latency_ms`；S1 实测 L1 ~150ms（桩模型） |
| 不越权 | token 换身份、工具透传 token、越权回 404 | `test_api.py` 越权用例、e2e「越权读会话 404」 |
| 可恢复 | `id:` 游标 + `Last-Event-ID` 续传 | 三种续传方式结果等价 |
| 不失控 | hop 上限 + 调用预算 + 运行超时 | `test_gateway.py` / `test_graph_l2.py` |
| 可审计 | `agent_run/step` + `tool_call_log(args_digest)` | 审计只存摘要的断言 |
| 可替换 | 分层 + 依赖注入 | 换 `ChatModel`/`AgentRepository` 不改业务 |
| 可观测 | `x-request-id` + 单行 JSON 日志 + `/readyz` | `test_observability.py`（10 例）；真进程日志实测含 `request_id/user_id/run_id` |

## 10. 扩展点

**加一个工具（五步）**：定义 `args_model` → 写 `handler(ctx, args)` → 声明 `side_effect` → 注册进 registry → 在 `evals/cases.jsonl` 补用例。网关与审计自动生效，不用改图。

**接真数据源**：`tools/client.py` 的 `BackendClient` 已经透传 token，新端点只需加方法；不要在工具里直连数据库。

**上 MySQL**：`PET_AGENT_REPO_BACKEND=mysql` + DSN；契约测试用 `PET_AGENT_TEST_MYSQL_DSN` 一并跑。

## 11. 非目标（S1.5 明确不做）

- 多 Agent 协作 / 子图编排（当前单 Agent 足够覆盖 L1+L2）；
- 长期记忆表（`memory_fact` / `memory_episode`）与画像抽取 —— S2；
- 文档/图片/视频 RAG —— S3；
- 写操作真执行（现在只回 `proposal`）—— 需产品确认审批链路；
- 管理端工作台、Langfuse 追踪、桌宠 —— 后续里程碑。
