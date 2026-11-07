# 规格：Agent Runtime HTTP/SSE 契约 v1.7

- 状态：Frozen（实现已按此验收；破坏性变更需升 v2）
- 日期：2026-11-08（v1.7 增 App 会话列表与 I22；v1.6 队列运维接口；v1.5 记忆最终一致；v1.4 幂等与熔断；v1.3 管理端）
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

`citations[]` 元素：`{kind, id, label, locator}`，`kind` 目前为 `log`（`locator` 是记录时间）或 `record`。
`steps[]` 元素：`{seq, kind, name, status, latency_ms, error}`。

### 4.4 事件顺序保证

1. `route` 一定先于任何 `delta`；
2. `tool` 一定落在它所属轮次之后、`done` 之前；
3. 终止事件只有一个（`done` 或 `error`）；
4. 客户端断开时服务端把 run 置 `cancelled`，不会留 `running` 僵尸。

## 5. `GET /agent/runs/{run_id}/events`

断线续传，只回放**内存缓冲**（`capacity=512`、`ttl=900s`）里的事件。

| 参数 | 位置 | 说明 |
| --- | --- | --- |
| `after` | query | 返回 `id > after` 的事件 |
| `Last-Event-ID` | header | `after` 缺省时使用；非数字按 0 处理 |

- 运行不存在 **或不属于当前用户** → `404 not_found`（不区分两者，避免探测）；
- 三种续传方式必须等价：全量 / `?after=N` / `Last-Event-ID: N`。

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
| `GET /agent/admin/usage` | `days`(7, 1–90) | `{days, runs, users, prompt_tokens, completion_tokens, total_tokens, avg_latency_ms, by_day:[{day,runs,tokens}]}` |

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

## 8. 验收用例（可执行）

```powershell
cd backend-agent
# 含真机仓储契约测试（需要 DSN，否则跳过 mysql 变体）
$env:PET_AGENT_TEST_MYSQL_DSN = "mysql://root:<本机口令>@127.0.0.1:3306/petlumina"
.\.venv\Scripts\python -m pytest              # 146 passed
.\.venv\Scripts\python -m evals.run           # routing 15/15, safety 6/6, memory 2/2
.\.venv\Scripts\python -m scripts.e2e_smoke       # 10/10
.\.venv\Scripts\python -m scripts.p1_smoke        # 9/9（配额/用量/记忆）
.\.venv\Scripts\python -m scripts.admin_smoke     # 6/6（管理端权限与列表/详情/用量）
.\.venv\Scripts\python -m scripts.idempotency_smoke  # 8/8（幂等键）
.\.venv\Scripts\python -m scripts.tasks_smoke        # 8/8（队列现场/死信重放）
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
