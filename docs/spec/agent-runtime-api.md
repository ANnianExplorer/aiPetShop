# 规格：Agent Runtime HTTP/SSE 契约 v1.18

- 状态：Frozen（实现已按此验收；破坏性变更需升 v2）
- 日期：2026-11-21（v1.18 管理端按模型分账；v1.17 情景往事/错误码三语化；v1.16 提示词版本化；v1.15 记忆评测；v1.14 引用回跳；v1.13 断线续传；v1.12 退避重试；v1.11 宠物画像与 I33–I36；v1.10 管理端队列/记忆/图谱与 I30–I32；v1.9 记忆删除导出与 `/metrics`；v1.8 文档问答与 I23–I26；v1.7 App 会话列表与 I22；v1.6 队列运维接口；v1.5 记忆最终一致；v1.4 幂等与熔断；v1.3 管理端）
- 实现：`backend-agent/app/api/`
- 关联：[SDD](../sdd/pet-agent-sdd.md) · [ADR-0003](../adr/0003-sse-event-contract.md)

## 1. 范围

| 包含 | 不包含 |
| --- | --- |
| 健康检查、对话、运行事件续传、会话消息回读 | 管理端接口、知识库上传、写入类工具的执行 |

Base URL：dev `http://localhost:8099`；路径前缀 `/`（不带 `/api/v1`，网关层再补）。

## 2. 鉴权

| 项 | 规则 |
| --- | --- |
| 凭证 | 请求头 `satoken: <token>`，或 `Authorization: Bearer <token>` |
| 解析 | `auth_mode=backend` 时 Runtime 调 Java `GET /api/v1/auth/current` 换 `user_id`；`header` 模式仅 dev，读 `x-user-id` |
| 缺失/失效 | `401`，code `unauthorized` |
| 用户身份 | **只能来自凭证**；请求体里带 `user_id` 会被 `extra=forbid` 拒（422） |

## 3. `GET /healthz`

200：

```json
{
  "status": "ok",
  "repo": "memory",
  "model": "deepseek-chat",
  "model_configured": true,
  "tools": ["get_health_summary", "get_pet_profile", "search_logs"],
  "graph_ready": true,
  "auth_mode": "backend"
}
```

`model_configured=false` 或 `graph_ready=false` 时服务仍存活，但 `/agent/chat` 会立刻回 `model_not_configured`。

## 3.1 `GET /readyz`

区分「进程活着」（`/healthz`）与「能接流量」（本接口）。不带鉴权，供编排系统探活。

200（就绪）：

```json
{"status": "ready", "checks": {"repo": "ok", "model": "ok", "circuit:llm": "ok", "circuit:backend": "ok"}}
```

503（未就绪）：`checks` 里对应项给出原因，且**不返回堆栈**：

```json
{"status": "degraded", "checks": {"repo": "ConnectionError", "model": "ok", "circuit:llm": "ok", "circuit:backend": "open"}}
```

| 检查项 | 通过条件 | 失败取值 |
| --- | --- | --- |
| `repo` | 存储真正可用：内存版恒 ok；MySQL 版执行 `SELECT 1` | 异常类名（如 `ConnectionError`） |
| `model` | `PET_AGENT_LLM_API_KEY` 非空 | `not_configured` |
| `circuit:llm` / `circuit:backend` | 熔断器未打开（`closed` / `half_open`；`half_open` 允许探活） | `open` |

## 3.2 通用响应头与日志字段

| 项 | 规则 |
| --- | --- |
| `x-request-id` | 调用方可自带（≤64 字符）；缺失时服务端生成 `uuid4().hex` 并回写 |
| 日志 | 每行一条 JSON，必含 `ts/level/logger/msg`，并自动附加 `request_id`；有会话上下文时附加 `user_id` / `run_id` |
| 敏感数据 | 日志**不记录**消息原文，只记 `msg_chars`、`answer_chars`、`args_digest`(16 位摘要) |

## 4. `POST /agent/chat`

### 4.1 请求

```json
{ "message": "上次打疫苗是什么时候？", "session_id": "1794024057356000000", "pet_id": "5001", "channel": "app" }
```

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `message` | string | 是 | 1–4000 字符；服务端再 `strip()`，全空白 → 400 `invalid_request` |
| `session_id` | string? | 否 | ≤32；为空则新建会话 |
| `pet_id` | string? | 否 | ≤32；随工具上下文下发 |
| `channel` | enum | 否 | `app` / `web` / `internal`，默认 `app`；不在 `allowed_channels` → 403 `forbidden` |
| `client_message_id` | string? | 否 | ≤64，`^[A-Za-z0-9_-]{1,64}$`；**幂等键**，见 4.2 |

未知字段 → **422**（`extra=forbid`，防止前端偷偷传 `user_id`）。`client_message_id` 不合法（空格、中文、超长）同样 422。

### 4.2 响应

`200 text/event-stream`，头：`Cache-Control: no-cache`、`Connection: keep-alive`、`X-Accel-Buffering: no`，
以及配额头（`rate_limit_enabled=true` 时）：`X-RateLimit-Limit`（窗口上限）、`X-RateLimit-Remaining`（本窗口剩余）。

超配额时**不建立 SSE**，直接 `429`：

```json
{ "code": "rate_limited", "message": "请求太频繁，请稍后再试", "retryable": true,
  "detail": { "retry_after_s": 37, "scope": "chat", "limit": 20 } }
```

响应头必须带 `Retry-After`（秒，≥1）。

上游连续失败触发熔断时同样**不建立 SSE**，直接 `503`：

```json
{ "code": "circuit_open", "message": "模型服务暂时不可用，请稍后再试", "retryable": true,
  "detail": { "retry_after_s": 30, "breaker": "llm" } }
```

#### 幂等（`client_message_id`）

| 场景 | 行为 |
| --- | --- |
| 首次请求带 `client_message_id` | 正常执行；`done` 事件里**没有** `replayed` 字段 |
| 同用户、同 key 再次请求 | 不新建消息、不调模型、不计费；回放已有 run 的事件流，`done.replayed=true`，`run_id` 与首次相同 |
| 并发两个同 key 请求 | 库层唯一键 `(user_id, idempotency_key)` 兜底：败者走回放，不重复执行 |
| 事件日志已过期（TTL/进程重启） | 退化为按库内消息重建 `route` + `done`（`replay_mode="from_db"`），**不报错** |

去重维度是**用户**不是会话：首次请求可能失败在「会话还没建出来」之前，此时客户端只有 key、没有 `session_id`。
不同用户用同一个 key 互不影响。

每条事件：

```
id: 3
event: delta
data: {"text":"9月1日打过疫苗，"}

```

`id` 是该 run 内**从 1 单调递增**的序号，跨事件类型共用一个序列。

### 4.3 事件类型

| event | 载荷 | 出现次数 | 语义 |
| --- | --- | --- | --- |
| `route` | `{session_id, run_id, route, intent, reason}` | 恰好 1 次，且第一 | `route∈{L1,L2,L3}`；`reason` 形如 `greeting` / `keyword:vaccine` / `default` |
| `tool` | `{name, status, latency_ms}` | 0..N | 每个执行的工具一条；`status∈{ok,error}` |
| `delta` | `{text}` | 0..N | 增量文本，可能为空串以外的任意片段 |
| `done` | `{run_id, session_id, message_id, route, intent, answer, citations[], steps[], usage{prompt_tokens,completion_tokens}, latency_ms}` | 恰好 1 次，终止 | `answer` 是完整答案（前端以它为准） |
| `error` | `{code, message, retryable, detail?}` | 0 或 1 次，终止 | 出现即 run 失败 |

`citations[]` 元素：`{kind, id, label, locator}`。

- `kind` 目前为 `pet` / `health` / `log` / `post` / `doc`；
- **`locator` 是 App 内路由**（`/` 开头，见 v1.14）：`/pet-detail/{id}`、`/log/{id}`、`/post/{id}`、
  `/weekly-health-detail?petId=…&date=…`；`doc` 的 `locator` 是文档内的定位串，不是 App 路由。
- 前端只按「能否跳转」判断，不再按 `kind` 硬编码；没有路由形态 `locator` 的历史数据由前端按 `kind` 兜底。
`steps[]` 元素：`{seq, kind, name, status, latency_ms, error}`。

#### 4.3.1 错误码与客户端展示（v1.17 / S1.36）

`error.code` 是稳定契约：客户端**按 code 映射文案**，不得解析 `message` 做分支。

| code | 常见来源 | App 文案 key | 可重试 |
| --- | --- | --- | --- |
| `invalid_request` / `invalid_arguments` | 请求体、工具参数不合法 | `agentError.invalidRequest` / `agentError.invalidArguments` | 否 |
| `unauthorized` / `forbidden` / `not_found` | 鉴权、越权、资源不存在 | `agentError.unauthorized` / `agentError.forbidden` / `agentError.notFound` | 否 |
| `tool_not_allowed` / `tool_failed` | 工具白名单、工具执行失败 | `agentError.toolNotAllowed` / `agentError.toolFailed` | `tool_failed` 是 |
| `backend_error` / `model_error` / `model_not_configured` | 后端、模型、模型未配置 | `agentError.backendError` / `agentError.modelError` / `agentError.modelNotConfigured` | 前两者是 |
| `run_timeout` / `budget_exceeded` | 运行超时、预算/配额耗尽 | `agentError.runTimeout` / `agentError.budgetExceeded` | `run_timeout` 是 |
| `rate_limited` | 限流；`detail={retry_after_s,scope,limit}` | 有秒数用 `agentError.rateLimitedWithRetry`，否则 `agentError.rateLimited` | 是 |
| `circuit_open` | 熔断；`detail={retry_after_s,breaker}` | 有秒数用 `agentError.circuitOpenWithRetry`，否则 `agentError.circuitOpen` | 是 |

- HTTP `401`/`403`/`404`/`408`/`429`/`5xx` 走同一套映射（客户端以 `http_<status>` 伪 code 复用）。
- `detail.retry_after_s` 是秒数（可能为小数），展示前**向上取整**；缺失、非数字或 `<= 0` 时退回「稍后再试」。
- 客户端不认识的 code 展示服务端 `message`；`message` 为空时展示 `agentError.unknown`，避免空白错误条。
- `message` 仍是中文兜底、不承诺多语言；三语文案由 App 的 `agentError.*` 命名空间维护，新增 code 必须同时补三种语言。

### 4.4 事件顺序保证

1. `route` 一定先于任何 `delta`；
2. `tool` 一定落在它所属轮次之后、`done` 之前；
3. 终止事件只有一个（`done` 或 `error`）；
4. **客户端断开不取消运行**（v1.13 起，S1.23）：连接的关闭只结束"这一次观读"，run 由进程内的 supervisor 继续跑完并写好 `done`，事件仍按 `id` 落进日志；只有进程退出才会把它收成 `cancelled`。客户端据此可以用 `?after=N` 接回同一轮，而不必重发消息。

## 5. `GET /agent/runs/{run_id}/events`

断线续传，只回放**事件缓冲**（默认 `capacity=512`、`ttl=900s`；Redis 后端同理，见 ADR-0003）里的事件。

| 参数 | 位置 | 说明 |
| --- | --- | --- |
| `after` | query | 返回 `id > after` 的事件 |
| `Last-Event-ID` | header | `after` 缺省时使用；非数字按 0 处理 |
| `follow` | query | `1` = 挂到本轮终止（v1.13）；缺省/`0` = 只读一次的快照，行为与 v1.12 一致 |

- 运行不存在 **或不属于当前用户** → `404 not_found`（不区分两者，避免探测）；
- 三种续传方式必须等价：全量 / `?after=N` / `Last-Event-ID: N`；
- `follow=1` 的结束条件只有三个：读到 `done`/`error`、库里 run 已非 `running` 且日志无新事件、超过 `run_follow_timeout_s`（默认 90s，客户端应重连）。轮询间隔 `run_follow_poll_s`（默认 0.05s）。

## 6. `GET /agent/sessions/{session_id}/messages`

| 参数 | 默认 | 约束 |
| --- | --- | --- |
| `limit` | 50 | 1–200，取最新 N 条后按时间正序返回 |

200：

```json
{ "session_id": "1794024057356000000", "messages": [
  { "id": "1794024057356000001", "role": "user", "content": "上次打疫苗是什么时候？", "run_id": null, "citations": [], "create_time": "2026-11-07 12:00:00" },
  { "id": "1794024057356000009", "role": "assistant", "content": "9月1日打过疫苗……", "run_id": "1794024057356000002", "citations": [{"kind":"log","id":"7001","label":"疫苗记录","locator":"2026-09-01 10:20:00"}], "create_time": "2026-11-07 12:00:01" }
] }
```

只返回 `user` / `assistant`（不含 system、tool）；他人会话 → `404`。

## 6.1 `GET /agent/memory/me`

我这个账号（可限定某只宠物）的长期事实记忆。用于"它到底记住了什么"、抽取质量核对与排障。

| 参数 | 默认 | 约束 |
| --- | --- | --- |
| `pet_id` | 空 | ≤32；为空表示不带宠物维度的事实 |
| `limit` | 20 | 1–50，按 `confidence DESC, update_time DESC` |

200：

```json
{ "pet_id": null, "facts": [
  { "id": "1794025553768000002", "key": "allergy", "label": "过敏", "value": "牛奶",
    "confidence": 0.95, "update_time": "2026-11-07 12:25:53" }
] }
```

> **一致性**：`PET_AGENT_TASK_BACKEND=memory|redis` 时，记忆写入走旁路任务队列，本接口是**最终一致**（通常亚秒级，崩溃重试时更久）。`off` 时写入在响应前完成。客户端不要"写完立刻断言可见"，验收脚本要轮询（见 `scripts/p1_smoke.py` 的 `wait_for_facts`）。

### 6.1.1 情景往事（v1.17 / BACKLOG C1）

用户说过的「已经发生的事」单独存成情景，用于回答「上次洗澡是什么时候」这类问题。与 6.1 的事实记忆互补：事实是「它是什么样」，情景是「发生过什么」。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/agent/memory/me/episodes?pet_id=&limit=` | 本人（可限定宠物）的往事，按 `occurred_at DESC, create_time DESC`；`limit` 1–50，默认 20 |
| DELETE | `/agent/memory/me/episodes/{episode_id}?pet_id=` | 删除本人一条往事；不存在/不属于本人 → `404 not_found` |

200（列表）：

```json
{ "pet_id": null, "episodes": [
  { "id": "1794025553768000003", "kind": "bath", "label": "洗澡",
    "summary": "上周给豆豆洗澡了", "occurred_at": "2026-11-12 00:00:00",
    "source_message_id": "1794025553768000001", "session_id": "1794025553768000000",
    "create_time": "2026-11-19 22:05:00" }
] }
```

约定：

1. **一条用户消息最多一个情景**；`source_message_id` 是写入它的那条用户消息，`(user_id, source_message_id)` 唯一，队列重复投递不会写两行。
2. **只记已发生的事**：问句、否定句、习惯句不记；没有时间词时必须有「了/过/刚/已经」等完成标记。相对时间（上周/上个月/N 天前）按自然日近似，`occurred_at` 只精确到日。
3. **召回是确定性规则**：事件类型命中 + 中文字符重叠 + 90 天新鲜度，阈值 0.50（类型必须命中），最多注入 3 条；没有向量库，语义改写召回不了。
4. **注入位置是 system prompt**：在事实块之后追加「与这次问题相关的往事」，每行带日期、类型、原话与来源消息 id；召回失败降级为不注入。
5. **导出升 v2**：`GET /agent/memory/me/export` 返回 `{version:2, ..., facts:[...], episodes:[...]}`；v1 消费方可忽略新字段。

## 6.2 `GET /agent/usage/me`

| 参数 | 默认 | 约束 |
| --- | --- | --- |
| `days` | 7 | 1–90，按 `agent_run.create_time` 过滤 |

200：`{days, runs, prompt_tokens, completion_tokens, total_tokens, avg_latency_ms}`，只统计 `status='succeeded'` 的 run。

## 6.3 管理端只读接口（S1.7）

前缀 `/agent/admin/`，**全部要求 token 解析出的 `role == "admin"`**；非管理员 `403 forbidden`（`{"code":"forbidden","message":"需要管理员权限"}`），无 token `401`。角色只来自 `GET /api/v1/auth/current` 的 `role` 字段——**请求头里的 `x-user-role` 在 backend 模式下被忽略**（header 模式仅 dev 可用，见 `config.auth_mode`）。

| 接口 | 参数 | 200 返回 |
| --- | --- | --- |
| `GET /agent/admin/sessions` | `page`(1) / `page_size`(10, ≤50) / `user_id?` / `q?`（标题包含，忽略大小写） | `{total, page, page_size, items:[{id,user_id,pet_id,channel,title,message_count,create_time}]}`，按最后活跃时间倒序 |
| `GET /agent/admin/sessions/{id}` | — | `{session, messages:[{id,role,content,run_id,citations,create_time}], runs:[{id,route,intent,status,prompt_tokens,completion_tokens,total_tokens,latency_ms,error,steps:[{seq,kind,name,status,latency_ms,error}]}]}`；未知会话 `404` |
| `GET /agent/admin/memory` | `user_id`（必填）/ `pet_id?` | `{pet_id, facts:[{id,key,label,value,confidence,update_time}]}` |
| `GET /agent/admin/usage` | `days`(7, 1–90) | `{days, runs, users, prompt_tokens, completion_tokens, total_tokens, avg_latency_ms, by_day:[{day,runs,tokens}], by_model:[{model,runs,prompt_tokens,completion_tokens,total_tokens,cost_usd}]}` |

`by_model` 只统计 `succeeded` 的 run，模型取 `agent_run.model`，空值归为 `unknown`；同一 `days` 口径下各行 runs/token 之和等于顶层总量。`cost_usd` 是按 `PET_AGENT_MODEL_PRICES`（JSON，USD / 1M tokens，如 `{"deepseek-chat":{"input_per_mtok":0.27,"output_per_mtok":1.10}}`）估算的展示值，四舍五入到 6 位小数；未配置该模型单价时为 `null`，不是 0。价格是部署配置快照，历史成本会随配置重算。

审计：每次读取**他人**会话或记忆都写一条 `admin.access` 日志，字段 `admin_id`、`target_user`、`session_id`（记忆为 `scope=memory`），**不记录消息正文与记忆值**。

## 6.4 管理端队列运维接口（S1.9）

旁路任务队列的现场与死信重放。同样要求 `role == "admin"`。

| 接口 | 参数 | 返回 |
| --- | --- | --- |
| `GET /agent/admin/tasks` | — | `{enabled, backend, processed, failed, topics:[{topic, depth, dead_letters}]}`；`TASK_BACKEND=off` 时 `enabled=false`、计数为 0（不是故障） |
| `POST /agent/admin/tasks/dead-letters/replay` | body `{topic, limit}`（`limit` 1–100，默认 10） | `{topic, replayed}`；未知 topic `400`，队列未启用 `404` |

约定：

- 重放把死信搬回待消费队列，**`attempt` 重置为 1**（否则消费失败一次就又进死信）；
- 重放本身写 `admin.access`，`scope=tasks.replay:<topic>`；
- 死信列表只留最近 `TASK_MAX_ATTEMPTS` 轮之后的条目，不做无限堆积（超过 `limit` 的留在死信里，可多次重放）。

## 6.5 我的会话列表（S1.10 / BACKLOG A2）

App 的历史入口。只返回 **token 解析出的本人**会话，不接受 `user_id` 参数（传了也没用）。

| 接口 | 参数 | 返回 |
| --- | --- | --- |
| `GET /agent/sessions` | `page`（≥1，默认 1）、`page_size`（1–50，默认 20） | `{total, page, page_size, items:[{id, pet_id, channel, title, message_count, create_time}]}` |

约定：

- 排序按会话**最后一条消息**时间倒序；同一秒内建立的两个会话按 id 倒序（雪花号），与 MySQL 的 `ORDER BY last_message_time DESC, id DESC` 同语义；
- 摘要里**不含 `user_id`**：本来就是自己的数据，前端不需要，也避免把别人 id 带出去；
- `total` 是全量条数，不是当前页条数（前端分页要用它）；
- 没有 token → `401`；分页参数越界 → `422`。

## 6.6 文档问答（S1.15 / BACKLOG A3）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/agent/documents/capabilities` | 能力矩阵：`text/pdf/image/video` 各自 `supported` + `suffixes` + `reason`，另有 `embedder` 与 `max_bytes` |
| POST | `/agent/documents` | `multipart/form-data`：`file`（必填）、`pet_id`（可选）；`202` 返回文档记录（`status=0` 排队） |
| GET | `/agent/documents` | 本人文档列表（`limit` 1–100，默认 50），按创建时间倒序 |
| GET | `/agent/documents/{id}` | 单条详情；他人的 id 返回 `404 not_found` |
| DELETE | `/agent/documents/{id}` | 软删除文档并物理删除其切片；返回 `{"deleted": true}` |

约定：

1. **状态语义**：`0` 排队 / `1` 解析中 / `2` 就绪 / `3` 失败 / `4` 不支持；`3`、`4` 必带人类可读的 `error`（例如"本机未安装 OCR（tesseract）"）。
2. **异步解析**：`TASK_BACKEND != off` 时上传只入队（`agent.doc.ingest`），由 worker 解析；`off` 时同步解析后返回——两种模式的对外语义一致，客户端都以 `status == 2` 为可检索标志。
3. **检索入口只有工具**：`search_docs(query, top_k)` 由模型在对话中调用，命中结果以 `citation.kind == "doc"` 回传（`locator` 为 `offset=N` / `page=N` / `t=12s`）；不提供公开的"检索"HTTP 接口，避免绕过工具网关。
4. **能力探测失败要给原因**：缺 `tesseract`/`ffmpeg` 时图片/视频标记不支持，前端据此禁用入口并显示原因，而不是上传后才报错。

## 6.7 记忆自主与运行指标（S1.16 / BACKLOG B3·B5·B7）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| DELETE | `/agent/memory/me?key=&pet_id=` | 删除本人一条事实（物理删除）；不存在返回 `404 not_found` |
| GET | `/agent/memory/me/export?pet_id=` | 导出本人全部事实与往事：`{version:2, exported_at, pet_id, facts:[...], episodes:[...]}` |
| GET | `/metrics` | Prometheus 文本（`text/plain; version=0.0.4`），**不加鉴权**，不含任何用户内容 |

约定：

1. **只作用于本人**：`user_id` 只从 token 解析，不接受参数；他人数据既不出现也删不动。
2. **删除是物理删除**：用户行使删除权，不留影子行；需要留底请先调导出接口。
3. **指标标签只放低基数字段**：`method` / 路由模板 `path` / `status` / `route` / `tool` / `direction`；绝不放 `session_id`、`user_id`、消息正文。
4. **在途消息可见性超时**：消费者取走消息后登记 `claimed`（score = 取用时刻），超过 `TASK_VISIBLE_TIMEOUT_S` 未 ack 的消息由巡检搬回主队列且 `attempt + 1`；这是 at-least-once 语义，消费端必须幂等。

## 6.8 管理端运维与图谱（S1.17 / BACKLOG B6）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/agent/admin/tasks` | 队列现场：`{enabled, backend, processed, failed, topics:[{topic, depth, dead_letters}]}` |
| POST | `/agent/admin/tasks/dead-letters/replay` | 死信放回：`{topic, limit}` → `{topic, replayed}`；`attempt` 归零 |
| DELETE | `/agent/admin/memory?user_id=&key=&pet_id=` | 管理员物理删除某用户的某条事实：`{deleted, key}`；不存在 `404` |
| GET | `/agent/admin/graph?user_id=&pet_id=&sessions=&runs_per_session=` | 三层视图：宠物节点 + 记忆事实节点 + 最近运行节点及边 |

约定：

1. **全部需要 `role == "admin"`**：`/agent/admin/**` 统一走 `_admin_identity`；backend 模式下 `role` 只来自 Java `/auth/current`，请求头一律忽略。
2. **图谱只画 Agent 自己库里的数据**（`memory_fact` / `agent_run`），不反查 Java 业务库——业务真源在 Java，跨服务拼图容易把权限边界拼漏。
3. **图谱规模有上限**：事实最多 50 条，会话最多 10 个、每会话最多 10 轮；超出部分不画（避免前端力导向图卡死）。
4. **管理端写操作必须审计**：删记忆记 `admin.access` 且 `scope="memory.delete"`，看图记 `scope="graph"`，只记关系不记正文。

## 6.9 宠物画像（S1.18 / BACKLOG C2）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/agent/profile/me?pet_id=` | 本人当前画像：`{id, pet_id, version, fact_count, confidence, create_time, stale, data}`；从未生成过 `404` |
| POST | `/agent/profile/me/refresh?pet_id=` | 强制重算并返回新版本（版本号单调 +1） |
| GET | `/agent/admin/profile?user_id=&pet_id=` | 管理员查看他人画像；不存在 `404`；读操作必留审计 |
| GET | `/agent/admin/profile/versions?user_id=&pet_id=&limit=` | 版本历史（新→旧），`limit` 1–20 |

画像 `data` 的固定结构（**字段要么有值、要么整组不出现**，不做占位）：

```
basics      { name?, age?, weightKg?, weightRaw? }
traits      { appetite? }
preferences { likes?: string[], avoids?: string[] }
riskFlags   [{ text, severity, evidence }]
careGaps    [{ text, reason? }]
evidence    [{ factId, key, label, value, confidence }]
meta        { factWatermark, builtAt }
```

约定：

1. **只由已确认事实生成**：输入是 `memory_fact` 中 `confidence >= 0.7` 的事实，同一 key 取置信度最高的一条；没有事实的字段不输出，不拿模型"编"。
2. **确定性**：同一批事实重复构建必须产出同一份 `data`（除 `meta.builtAt`）；因此 builder 是纯函数，不调模型。
3. **可追溯**：`evidence` 每条都带 `factId`，管理端可点回事实；删掉事实后重建，结论随之消失。
4. **过期标记而非静默旧值**：`stale=true` 表示「事实比画像新」，前端必须显式提示；判定用 `meta.factWatermark` 与 `memory_fact` 的最大 `update_time` 比较。
5. **因果顺序**：重算挂在记忆消费之后（同一个 consumer），不允许与记忆写入并发——否则会产出 `fact_count=0` 的空画像。

## 6.10 任务重试与多副本语义（S1.19 / BACKLOG B4·B2）

**重试（B4）**：`nack` 后消息先进**退避队列**（Redis `{prefix}:{topic}:retry` ZSET，score = 到期时刻），
`backoff = min(base * 2^(attempt-1), cap)`（默认 `base=5s`、`cap=600s`），巡检到期后搬回主队列并 `attempt+1`；
超过 `max_attempts` 进死信。**`depth(topic)` 只统计主队列**，不含退避与死信——看积压不要漏看这两个数。

| 配置 | 默认 | 语义 |
| --- | --- | --- |
| `TASK_RETRY_BASE_S` | 5 | 首次退避秒数 |
| `TASK_RETRY_CAP_S` | 600 | 退避上限 |
| `TASK_DLQ_REDRIVE_INTERVAL_S` | 0 | 死信自动重投周期；**0 = 关闭** |
| `TASK_DLQ_MAX_REDRIVES` | 3 | 同一条消息最多被自动重投几次（`redrives` 字段） |
| `TASK_DLQ_REDRIVE_LIMIT` | 5 | 每轮每 topic 最多重投几条 |

约定：

1. **重投也有上限**：`redrives` 达到上限的留在死信等人处理，不做"无限自动重试"；
2. **自动重投默认关闭**：打开是显式运维决策，必须在变更单里写清下游修好了什么；
3. **at-least-once**：重复投递由消费端幂等兜底（审计按事件 id `INSERT IGNORE`、记忆按唯一键 upsert）。

**多副本（B2）**：两个副本共享 MySQL + Redis 时

| 能力 | 是否共享 | 依据 |
| --- | --- | --- |
| 任务消费（不重复） | ✅ | 队列在 Redis，`BRPOPLPUSH` 抢占 |
| 事件回放 | ✅ | `RedisEventStore` 跨副本可读 |
| 限流窗口 | ✅ | `RedisRateLimiter` 按用户计数 |
| 幂等键 | ✅ | `agent_run` 唯一键 `(user_id, idempotency_key)` |
| 熔断状态 | ❌（已知限制） | 进程内 `CircuitBreaker`，多副本各自熔断 |

验收：`python -m scripts.multi_replica_smoke`（两个副本 8 项全过）。

## 7. 不变量（必须永远成立）

| 编号 | 断言 | 验证 |
| --- | --- | --- |
| I1 | 会话/运行/消息都归属于 token 解析出的 `user_id` | `test_api.py::test_other_user_session_404` |
| I2 | 单个 run 的工具执行次数 ≤ `max_tool_calls_per_run`，超了回 `budget_exceeded` | `test_gateway.py` |
| I3 | 工具参数里出现 `user_id` 一律拒绝（422/`invalid_arguments`） | `test_gateway.py::test_schema_has_no_user_id` |
| I4 | 副作用工具默认不出现在 schema 里；需确认时只回 `proposal` | `test_gateway.py::test_side_effect_tool_hidden_by_default` |
| I5 | 每个 run 最终状态 ∈ {succeeded, failed, cancelled} | `test_repository_contract.py` |
| I6 | `steps.seq` 连续（1,2,3…），`agent_message` 只含 user/assistant | `test_repository_contract.py` |
| I7 | 审计只存参数摘要（sha256 前 16 位），不存原文 | `test_gateway.py::test_audit_stores_digest_only` |
| I8 | `done.usage` = 图内累计 + 流式 usage（不重不漏） | `test_api.py::test_l1_event_sequence` |
| I9 | 每个响应都带 `x-request-id`（自带则原样回传，超 64 字符截断） | `test_observability.py::test_request_id_propagated_from_caller` |
| I10 | 存储不可用或模型未配置时 `/readyz` 返回 503，且不回堆栈 | `test_observability.py::test_readyz_*` |
| I11 | 超配额返回 `429 rate_limited` + `Retry-After`，且**不产生** run/消息（不落库、不计费） | `test_api.py::test_rate_limit_returns_429_with_retry_after` |
| I12 | 记忆只从**本人**对话抽取，只能被本人召回；同一 `(user, pet, key)` 只有一条 | `test_memory.py::test_memory_is_isolated_by_pet_and_user`、`test_memory_fact_upsert_dedupes_by_key` |
| I13 | 记忆写入/召回失败不影响本轮回答（降级为无记忆） | `app/runtime/runner.py` 的 `_recall`/`_observe` 兜底；`test_api.py::test_recalled_memory_is_injected_into_system_prompt` |
| I14 | `/agent/admin/**` 只有 `role == "admin"` 可访问；伪造 `x-user-role` 在 backend 模式无效 | `test_admin.py::test_forged_role_header_is_ignored` |
| I15 | 管理端读取他人数据必留 `admin.access` 审计，且不落正文 | `test_admin.py::test_admin_detail_audit_log` |
| I16 | 同用户同 `client_message_id` 重试只执行一次：不重复调模型、不重复落消息、不重复计费 | `test_idempotency.py::test_same_key_does_not_execute_twice`、`scripts.idempotency_smoke` |
| I17 | 熔断打开后新请求快速失败 `503 circuit_open` + `Retry-After`，**不再打下游**；401/422 不计入失败 | `test_circuit.py::test_opens_after_threshold_and_fails_fast`、`test_client_errors_do_not_trip_breaker` |
| I18 | 熔断打开时 `/readyz` 返回 503 且 `checks["circuit:*"] == "open"`，`/healthz` 仍 200 | `test_circuit.py::test_readyz_reports_open_circuit` |
| I19 | 进程启动时先把「在途」消息搬回队列再开消费，崩溃不丢任务 | `test_task_queue.py::test_recover_returns_inflight_messages`；真机日志 `task inflight recovered on startup` |
| I20 | 死信重放后 `attempt` 归零，否则一次失败又立刻进死信 | `test_task_queue.py::test_replay_dead_letter_resets_attempt` |
| I21 | 队列现场与死信重放只有 `role == "admin"` 可访问 | `test_admin.py::test_admin_replays_dead_letters` |
| I22 | `GET /agent/sessions` 只返回本人会话；他人会话不出现在列表里，`user_id` 不出现在载荷里 | `test_sessions_api.py::test_sessions_are_isolated_by_user` |
| I23 | 文档上传/查询/删除都只作用于本人文档；他人 `document_id` 一律 404（不泄露存在性） | `test_rag.py::test_document_is_isolated_by_user` |
| I24 | 检索只召回本人切片（`user_id` 隔离），且只召回 `is_delete=0` 的文档 | `test_rag.py::test_search_isolated_by_user`、`test_deleted_document_is_not_searchable` |
| I25 | 上传状态语义固定：0 排队 / 1 解析中 / 2 就绪 / 3 失败（带原因）/ 4 不支持（带原因） | `test_rag.py::test_unsupported_video_reports_reason` |
| I26 | 超过 `doc_max_bytes` 的上传直接拒绝；同一文件重复上传复用同一条记录（删除后重传亦复活） | `test_rag.py::test_oversized_upload_rejected`、`scripts.rag_smoke`（第二次运行命中同一 id） |
| I27 | 记忆删除/导出只作用于本人；他人既查不到也删不动（返回 404，不泄露存在性） | `test_memory_api.py::test_memory_is_isolated_between_users` |
| I28 | `/metrics` 的路由标签用模板而非原始 URL，且输出中不含用户内容 | `test_metrics.py::test_http_metrics_use_route_template`、`test_metrics_endpoint_renders_prometheus_text` |
| I29 | 取走超过可见性超时仍未 ack 的消息必须被巡检搬回（`attempt + 1`），ack 过的不得被误搬 | `test_task_queue.py::test_sweep_reclaims_stale_inflight`、`test_sweep_ignores_acked_messages` |
| I30 | 管理员删除记忆同样只删指定用户指定 key 的一条，且必留 `admin.access`（`scope="memory.delete"`） | `test_admin.py::test_admin_deletes_user_memory_with_audit` |
| I31 | 管理端图谱三层齐全：1 个宠物节点 + N 个事实节点 + M 个运行节点，所有边都从宠物节点出发 | `test_admin.py::test_admin_graph_has_three_layers` |
| I32 | 图谱只读 Agent 侧数据，不因 Java 侧字段缺失而 500；规模受 `sessions`/`runs_per_session` 上限约束 | 同上（上限参数在 6.8 约定 3） |

| I33 | 画像只由 `confidence >= 0.7` 的事实生成；无事实的字段不出现（不臆造） | `test_profile.py::test_builder_omits_unknown_sections`、`test_builder_ignores_low_confidence` |
| I34 | 同一批事实重复构建结果一致（除 `meta.builtAt`） | `test_profile.py::test_builder_is_deterministic` |
| I35 | 事实更新后画像标 `stale=true`，重建后清除 | `test_profile.py::test_profile_marks_stale_when_new_fact_arrives` |
| I36 | 画像只有本人可读；管理端读取他人画像需 admin 且留 `admin.access`（`scope="profile"`） | `test_profile.py::test_profile_isolated_between_users`、`test_admin_reads_other_users_profile_with_audit` |
| I37 | 任务失败先进退避队列（不在主队列），到期才搬回；退避时间随次数指数增长并封顶 | `test_task_queue.py::test_retry_not_promoted_before_due`、`test_backoff_grows_and_caps` |
| I38 | 死信自动重投默认关闭，且同一条消息最多重投 `max_redrives` 次（按 `redrives` 字段计） | `test_task_queue.py::test_redrive_dead_letters_respects_max_redrives` |
| I39 | 多副本共享 MySQL/Redis 时：同一任务只被消费一次、事件跨副本可回放、幂等与限流跨副本一致 | `scripts.multi_replica_smoke`（8/8） |
| I40 | 关闭 SSE 消费端**不取消**运行：run 仍跑到 `succeeded`，事件日志恰好一条 `done` 且在末尾 | `test_reconnect.py::test_closing_consumer_does_not_cancel_run` |
| I41 | `?follow=1` 从任意 `after` 续传时事件 id 严格递增、不重不漏，末尾必是终止事件 | `test_reconnect.py::test_follow_returns_events_after_cursor`、`test_follow_waits_for_running_run` |
| I42 | 不带 `follow` 的 `/events` 仍是快照语义；幂等回放路径原样转发、不接管成跟随 | `test_reconnect.py::test_snapshot_stays_snapshot_without_follow`、`test_idempotent_replay_still_forwards` |
| I43 | `citations[].locator` 是 App 内路由（`/` 开头），前端据此跳转；`doc` 例外（文档内定位串） | `test_citations.py::test_every_locator_is_an_app_route`、`citationRoute.spec.ts` |
| I44 | 情景按 `(user_id, source_message_id)` 幂等；同一消息重复投递只一行，不同用户/宠物互不可见 | `test_memory_episodes.py::test_record_episode_is_idempotent_by_source_message`、`test_repository_contract.py::test_memory_episode_dedupes_by_source_message` |
| I45 | 回忆往事必须带发生日期与来源消息 id，且只注入类型命中的情景；问句/否定/习惯不写入 | `test_api.py::test_conversation_recalls_episode_with_source_message_id`、`test_memory_episodes.py::test_episode_lines_recall_matching_event_only` |
| I46 | `error.code` 是稳定契约：App 对已知 code 用 `agentError.*` 本地化，未知 code 才展示服务端 message；`retry_after_s` 向上取整 | `agentError.spec.ts`、`ChatView.error.spec.ts` |
| I47 | `by_model` 与顶层用量同口径：各行 runs/token 之和等于总量，空模型归 `unknown`；未配置单价时 `cost_usd=null`（不按 0 计） | `test_admin.py::test_admin_usage_overview`、`test_admin.py::test_admin_usage_by_model_cost` |

## 8. 验收用例（可执行）

```powershell
cd backend-agent
# 含真机仓储契约测试（需要 DSN，否则跳过 mysql 变体）
$env:PET_AGENT_TEST_MYSQL_DSN = "mysql://root:<本机口令>@127.0.0.1:3306/petlumina"
.\.venv\Scripts\python -m pytest              # 290 passed + 1 skipped（未开 DSN；开 DSN 另跑 MySQL 契约变体）
.\.venv\Scripts\python -m evals.run           # routing 15/15, safety 6/6, memory 48/48
.\.venv\Scripts\python -m scripts.e2e_smoke       # 10/10
.\.venv\Scripts\python -m scripts.p1_smoke        # 9/9（配额/用量/记忆）
.\.venv\Scripts\python -m scripts.admin_smoke     # 6/6（管理端权限与列表/详情/用量）
.\.venv\Scripts\python -m scripts.idempotency_smoke  # 8/8（幂等键）
.\.venv\Scripts\python -m scripts.tasks_smoke        # 8/8（队列现场/死信重放）
.\.venv\Scripts\python -m scripts.rag_smoke          # 10/10（上传→解析→检索→引用→删除）
.\.venv\Scripts\python -m scripts.ops_smoke          # 11/11（指标/记忆导出删除/在途巡检）
.\.venv\Scripts\python -m scripts.multi_replica_smoke # 8/8（两个副本：事件/幂等/消费/限流）
.\.venv\Scripts\ruff.exe check .              # All checks passed
```

## 9. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| v1.0 | 2026-11-07 | 初版：从 S1.5 实现反推并冻结，含 I1–I8 不变量 |
| v1.1 | 2026-11-07 | 增 `/readyz`、`x-request-id`、日志字段约定与 I9–I10（S1.6 P0） |
| v1.2 | 2026-11-08 | 增 `/agent/memory/me`、`/agent/usage/me`、429 与配额头、I11–I13（S1.6 P1） |
| v1.3 | 2026-11-08 | 增 6.3 管理端只读接口、`admin.access` 审计、I14–I15（S1.7） |
| v1.4 | 2026-11-08 | 增 `client_message_id` 幂等语义、`503 circuit_open`、`/readyz` 熔断检查、I16–I18（S1.8 P2） |
| v1.5 | 2026-11-08 | `/agent/memory/me` 补一致性说明：`TASK_BACKEND=memory\|redis` 时写入最终一致（S1.9-a）；验收命令 122 passed、补 `idempotency_smoke` |
| v1.6 | 2026-11-08 | 增 6.4 队列运维接口（查看现场 + 死信重放）、I19–I21（启动补偿/重放归零/仅管理员）；验收命令 142 passed、补 `tasks_smoke`（S1.9-b） |
| v1.7 | 2026-11-08 | 增 6.5 我的会话列表 `GET /agent/sessions`（本人隔离/排序/分页语义）与 I22；验收命令 146 passed（BACKLOG A2） |
| v1.8 | 2026-11-08 | 增 6.6 文档问答接口（能力矩阵/上传/列表/详情/删除）、状态语义与 I23–I26；验收命令 169 passed、补 `rag_smoke`（BACKLOG A3 / S1.15） |
| v1.9 | 2026-11-08 | 增 6.7 记忆删除/导出与 `/metrics`、在途消息可见性超时语义、I27–I29；验收命令 181 passed、补 `ops_smoke`（BACKLOG B3·B5·B7 / S1.16） |
| v1.10 | 2026-11-08 | 增 6.8 管理端队列现场/死信重放/管理员删记忆/三层图谱、I30–I32；验收命令 183 passed（BACKLOG B6 / S1.17） |
| v1.11 | 2026-11-08 | 增 6.9 宠物画像（四个接口 + data 结构 + 五条约定）、I33–I36；验收命令 203 passed（BACKLOG C2 / S1.18） |
| v1.12 | 2026-11-08 | 增 6.10 任务退避重试（backoff/重投上限/默认关闭）与多副本语义（共享 vs 熔断单实例）；验收命令 208 passed、补 `multi_replica_smoke`（BACKLOG B4·B2 / S1.19） |
| v1.13 | 2026-11-14 | 4.4 第 4 条改为「断开不取消运行」；§5 增 `follow` 参数（挂到终止）与三个结束条件、`run_follow_timeout_s`/`run_follow_poll_s`；增 I40–I42；验收命令 202 passed + 1 skipped（MySQL 变体未开 DSN）、前端 `resilientChat.spec.ts` 8 例（BACKLOG B8 / S1.23） |
| v1.14 | 2026-11-14 | `citations[].locator` 明确为 App 内路由（`/pet-detail`、`/log`、`/post`、`/weekly-health-detail?petId=&date=`），新增只读工具 `search_posts` 提供帖子引用来源；增 I43；验收 216 passed + 1 skipped、App 141 tests、`e2e_smoke` 10/10（BACKLOG C4 / S1.25） |
| v1.15 | 2026-11-15 | memory 评测 2→48 条（`text`/`observe`/`turns` 三种用例形状），阈值 1.0→0.9，失败 note 区分 `wrong`/`extra`/`forbid_leaked`；抽取规则修 5 类缺陷；验收 221 passed + 1 skipped、`memory 48/48`（BACKLOG C3 / S1.27） |
| v1.16 | 2026-11-15 | **无接口变更**（本轮不动任何 HTTP/SSE 形状）：系统提示词改为版本登记表 + 冻结哈希，`prompt_version` 只进 `agent_message.meta` 与 `run finished` 日志；验收 228 passed + 1 skipped、`evals` 69 条全绿（BACKLOG D6 / S1.28） |
| v1.17 | 2026-11-21 | **无接口变更**：把 4.3 已有字段固化为客户端展示契约（4.3.1 错误码→三语文案、未知 code 回退、`retry_after_s` 向上取整）并增 I46；验收 283 passed + 1 skipped、App 176 tests（BACKLOG D8 / S1.36） |
| v1.17 | 2026-11-19 | 增 6.1.1 情景往事（`GET/DELETE /agent/memory/me/episodes`）、导出升 v2 并含 `episodes`、I44–I45；验收 283 passed + 1 skipped（未开 DSN）（BACKLOG C1 / S1.34） |
| v1.18 | 2026-11-21 | 6.3 `/agent/admin/usage` 增 `by_model`（模型、runs、prompt/completion/total、`cost_usd`）；单价由 `PET_AGENT_MODEL_PRICES` 配置，未配置为 `null`；增 I47；验收 290 passed + 1 skipped、管理端 `vue-tsc` 0 + build 0（BACKLOG D4 / S1.37） |
