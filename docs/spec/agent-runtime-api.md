# 规格：Agent Runtime HTTP/SSE 契约 v1.0

- 状态：Frozen（实现已按此验收；破坏性变更需升 v2）
- 日期：2026-11-07
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

未知字段 → **422**（`extra=forbid`，防止前端偷偷传 `user_id`）。

### 4.2 响应

`200 text/event-stream`，头：`Cache-Control: no-cache`、`Connection: keep-alive`、`X-Accel-Buffering: no`。

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

## 8. 验收用例（可执行）

```powershell
cd backend-agent
.\.venv\Scripts\python -m pytest          # 45 passed
.\.venv\Scripts\python -m evals.run       # routing 15/15, safety 6/6, memory 2/2
.\.venv\Scripts\python -m scripts.e2e_smoke   # 10/10
```

## 9. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| v1.0 | 2026-11-07 | 初版：从 S1.5 实现反推并冻结，含 I1–I8 不变量 |
