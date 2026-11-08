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

## 5. 数据模型（`backend/sql/v2.10-agent.sql` + `v2.11-agent-memory.sql`）

| 表 | 关键列 | 不变量 |
| --- | --- | --- |
| `agent_session` | `id`, `user_id`, `pet_id`, `title`, `message_count`, `status` | 会话有主；`user_id` 只能来自 token |
| `agent_message` | `id`, `session_id`, `role`, `content`, `citations_json`, `run_id` | 只存 `user`/`assistant`；正序 |
| `agent_run` | `id`, `session_id`, `user_id`, `status`, `route`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `error_code`, `idempotency_key` | 必须落到终态（succeeded/failed/cancelled）；唯一键 `(user_id, idempotency_key)` 保证「一条消息最多执行一次」 |
| `agent_step` | `id`, `run_id`, `seq`, `kind`, `name`, `status`, `latency_ms`, `error` | `(run_id, seq)` 连续 |
| `tool_call_log` | `id`, `run_id`, `tool_name`, `args_digest`, `ok`, `error_code`, `latency_ms` | 只存 sha256 前 16 位摘要，不存原文 |
| `memory_fact` | `id`, `user_id`, `pet_id`, `fact_key`, `fact_value`, `confidence`, `source` | 唯一键 `(user_id, pet_id, fact_key)`；`pet_id=0` 表示无宠物维度 |
| `memory_episode` | `id`, `user_id`, `pet_id`, `session_id`, `summary`, `detail`, `occurred_at`, `embedding_id` | 表内不存向量，只存向量库 ID |

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
| `BudgetExceeded` | `budget_exceeded` | 429 | 否 | 单 run 工具调用/token 超预算 |
| `RateLimited` | `rate_limited` | 429 | 是（等窗口） | 用户分钟/日配额用尽；带 `Retry-After` |
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
| `PET_AGENT_RUN_TOKEN_BUDGET` | `30000` | 单 run 累计 token 上限（0=不限） |
| `PET_AGENT_RATE_LIMIT_ENABLED` | `true` | 是否启用每用户配额 |
| `PET_AGENT_RATE_LIMIT_PER_MINUTE` | `20` | 每分钟对话次数 |
| `PET_AGENT_RATE_LIMIT_PER_DAY` | `300` | 每日对话次数 |
| `PET_AGENT_RATE_LIMIT_BACKEND` | `memory` | `memory`（单副本）/ `redis`（多副本共享） |
| `PET_AGENT_EVENT_BACKEND` | `memory` | `memory` / `redis`（Redis Stream，跨进程续传） |
| `PET_AGENT_REDIS_URL` | `redis://localhost:6379/0` | 事件流与配额共用 |
| `PET_AGENT_LOG_LEVEL` | `INFO` | 日志级别 |
| `PET_AGENT_CIRCUIT_THRESHOLD` | `5` | 连续失败多少次打开熔断 |
| `PET_AGENT_CIRCUIT_COOLDOWN_S` | `30` | 熔断冷却期，过后放一个探测请求 |

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

### 8.3 配额、事件总线与记忆（S1.6 P1）

| 子系统 | 模块 | 关键约定 |
| --- | --- | --- |
| 配额 | `app/core/ratelimit.py` | 分钟窗口 + 日窗口双计数；内存实现滑动窗口（`deque[float]`），Redis 实现 `INCR` + `EXPIRE`；Redis 故障 **fail-open** 放行并打 `rate limiter unavailable`；超限 → `429` + `Retry-After`，**不建 SSE、不落 run** |
| Token 预算 | `app/graph/nodes.py` | 每轮 `spent = prompt + completion + 本轮 reply.usage.total`，超 `run_token_budget` 抛 `BudgetExceeded`，run 落 failed |
| 事件总线 | `app/runtime/eventlog.py` | `EventStore` 协议两实现：内存（capacity 截断 + ttl 清理）与 Redis Stream（`INCR` 序号 → `XADD maxlen` → `EXPIRE`，读 `XRANGE`，坏 payload 跳过）；`after`/`Last-Event-ID` 语义两实现完全一致 |
| 记忆写入 | `app/memory/extract.py` + `ops.py` | 规则抽取（名字/年龄/体重/过敏/忌口/爱吃/疫苗）+ 置信度阈值；`ADD/UPDATE/NOOP` 三态，重复同一句话不产生第二条 |
| 记忆召回 | `app/memory/service.py` | 召回低置信度过滤后拼成 `标签：值` 进 system 提示；**不伪造 user 消息**；召回/写入异常一律吞掉，降级为无记忆 |
| 用量 | `storage.usage_summary` | 只统计 `succeeded`，按 `agent_session.user_id` 归属，`AVG(latency_ms)` |

记忆不进向量的边界：`memory_episode` 只存摘要与向量 ID，检索走外部向量库（S2）；事实记忆用精确键查询，不用语义检索——记错比记不住更贵。

### 8.4 管理端只读接入（S1.7）

| 关注点 | 落点 | 约定 |
| --- | --- | --- |
| 角色来源 | `app/api/deps.py` 的 `IdentityResolver` | 只信 `GET /api/v1/auth/current` 的 `role`；`x-user-role` 仅 `auth_mode=header`（dev）可用，生产忽略 |
| 授权点 | `app/api/routes.py::_admin_identity` | 统一 403 `需要管理员权限`；仓储层**不做权限判断**（协议注释写死"调用方必须先校验"） |
| 查询 | `app/storage/{memory,mysql}.py` | 四个只读方法：`list_sessions` / `get_session_any` / `list_runs` / `usage_overview`；MySQL 版 `list_runs` 用 `WHERE run_id IN (...)` 批量取 step，避免 N+1 |
| 分页 | `list_sessions` | `LIMIT/OFFSET` + `COUNT(*)` 同条件；排序按最后活跃时间，其次 id |
| 审计 | `agent.access` 日志 | 只记 `admin_id`/`target_user`/`session_id`，不记消息正文与记忆值 |
| 前端 | `pet-lumina-web/src/api/agent.ts` | 独立 axios 实例（Agent 是纯 REST，不是 Java 的 `{code,data,message}` 信封）；403/404 直接按 HTTP 状态处理 |

管理端只读是刻意的：**不允许管理员代发消息**。代发会污染用户会话与记忆归属，需要单独的产品与审计设计（S3 再议）。

### 8.5 韧性：幂等与熔断（S1.8 P2）

| 关注点 | 落点 | 约定 |
| --- | --- | --- |
| 幂等键 | `ChatRequest.client_message_id` | `^[A-Za-z0-9_-]{1,64}$`；非法在入口 422，不落库 |
| 去重维度 | `agent_run` 唯一键 `(user_id, idempotency_key)` | 按**用户**而不是会话：首次请求可能失败在会话建出来之前，此时客户端只有 key |
| 重试路径 | `AgentRunner.stream` 快路径 + `_replay` | 命中即回放事件流，`done.replayed=true`；不建消息、不调模型、不计费 |
| 事件缺失 | `_replay` 退化分支 | `eventlog` 已过期时按库内消息重建 `route` + `done`（`replay_mode="from_db"`），绝不报错 |
| 并发 | MySQL 唯一键 + `IntegrityError` 回查 | 败者拿到旧 run 并回放；内存实现用同语义的 `dict` 兜底 |
| 熔断 | `app/core/circuit.py` | 三态 `closed → open → half_open`；阈值 5、冷却 30s 可配；`half_open` 只放**一个**探测 |
| 熔断范围 | LLM 客户端与 Java 后端客户端各自一个 | 熔断器在 `create_app` 装配时创建并共享；按请求 new 永远打不开 |
| 失败计数口径 | `counts_as_failure` | 非 `AgentError` 一律算失败；`AgentError` 只算 `retryable=True`（401/403/422 是调用方问题，不熔断后端） |
| 暴露方式 | `503 circuit_open` + `Retry-After`；`/readyz` 的 `checks.circuit:*` | 快速失败不再打下游；liveness 不受影响 |
| Redis 兼容 | `app/core/redis_client.py` | 统一 `protocol=2`：Redis 5 不支持 RESP3 的 `HELLO`，用默认 RESP3 会直接连不上（真机抓到的 D1） |

### 8.6 旁路任务队列（S1.9）

| 关注点 | 落点 | 约定 |
| --- | --- | --- |
| 为什么 | 记忆抽取、审计落库不该占响应时间 | 首 token 延迟只受「召回 + 首轮模型」影响 |
| 协议 | `app/tasks/base.py::TaskQueue` | `publish` / `receive` / `ack` / `nack` / `depth` / `dead_letters`；**at-least-once** |
| 实现 | `InProcessTaskQueue`（内存）、`RedisTaskQueue`（LPUSH + BRPOPLPUSH + processing 列表）、`RocketMQTaskQueue`（待做，见 ADR-0009） | 只依赖 Redis 5.0 已有命令，不用 Stream consumer group |
| 投递失败 | 队列满/中间件挂 → `TaskQueueFull` | 调用方**立刻退回同步执行**，宁可慢也不丢 |
| 消费失败 | `TaskWorker` 重试，超过 `TASK_MAX_ATTEMPTS` 进死信 | 死信可查（`dead_letters`），对应日志 `task dead letter` |
| 崩溃恢复 | `RedisTaskQueue.recover_inflight` | 进程崩了 processing 里的消息搬回主列表，代价是可能重复一次 |
| 幂等 | 记忆按 `(user, pet, key)` upsert；审计消息 id 作 `tool_call_log.id` + `INSERT IGNORE` | 重复投递不会写两条 |
| 一致性 | 开启队列后记忆写入是**最终一致**（秒级） | `GET /agent/memory/me` 可能短暂读到旧值；`TASK_BACKEND=off` 时即时 |
| 默认值 | `TASK_BACKEND=off` | 行为与 S1.8 一致；生产按需显式打开，避免"悄悄变成异步" |
| 启动补偿 | `lifespan` 里先 `tasks.recover(TOPICS)` 再 `worker.start()` | 顺序反了会与 consumer 抢同一条消息；真机日志 `task inflight recovered on startup` |
| 死信重放 | `POST /agent/admin/tasks/dead-letters/replay` | `attempt` 重置为 1；未知 topic 400；写 `admin.access` 审计 |
| 现场可观测 | `GET /agent/admin/tasks` | `enabled/backend/processed/failed` + 每 topic 的 `depth` 与 `dead_letters`；`off` 时 `enabled=false` |

### 8.7 App 历史会话（BACKLOG A2）

| 关注点 | 落点 | 约定 |
| --- | --- | --- |
| 数据来源 | `AgentRepository.list_sessions(page, page_size, user_id)` | 复用 S1.7 管理端那套查询，只是把 `user_id` 固定为 token 解析出的本人 |
| 隔离 | 路由 `_identity()` → `user_id` 透传仓储 | 不接收请求体/查询里的 `user_id`；载荷里也不返回它 |
| 排序 | 内存版 `(last_active, id)` 倒序；MySQL 版 `ORDER BY last_message_time DESC, id DESC` | 同一秒建立的会话靠雪花 id 兜底，两端语义一致 |
| 分页 | `page` / `page_size`（1–50） | `total` 是全量条数 |
| 前端 | `ChatView.vue` 的「历史会话」底部面板；`fetchSessions()` | 每次打开都重拉；选中后清空气泡再回读消息，避免串会话 |
| 失败降级 | 401 → 清 token 跳登录；其他 → 面板内红字提示 | 不阻塞对话主流程 |

### 8.8 文档问答 RAG（S1.15 / BACKLOG A3）

| 关注点 | 落点 | 约定 |
| --- | --- | --- |
| 存储 | `doc_file`（元数据 + `uk_user_sha`）+ `doc_chunk`（切片 + 向量 `MEDIUMTEXT`） | 向量以 JSON 存 TEXT：本机没有 pgvector，先保证"能跑 + 可换" |
| 上传 | `POST /agent/documents`（multipart） | 20MB 上限、按 `sha256` 去重；同一文件删掉再传会"复活"原记录 |
| 解析 | `app/rag/parsers.py` | 文本按 utf-8→utf-8-sig→gb18030 递归解码；PDF 按页 `page=N`；图片/视频依赖 OCR/ffmpeg，缺失时 `status=4` 并给原因 |
| 切分 | `chunk_text(size=800, overlap=120)` | 段落→句子聚合，超长硬切，短尾块丢弃 |
| 嵌入 | `build_embedder(settings)`：`hash`（默认，零依赖确定性）/ `openai`（兼容 `/embeddings`） | 默认 hash 是"能离线跑通"的权宜，切换后端只需改 `PET_AGENT_EMBED_BACKEND` |
| 检索 | `DocumentService.search()`：查询向量 × 本人切片余弦，`min_score=0.05`，`top_k≤20` | 只取本人 + 未删除文档；结果转 `citation{kind:"doc"}` |
| 工具 | `search_docs(query, top_k)` | 与其它工具共用网关（白名单/参数校验/审计）；服务未装配时返回 `docs_unavailable` |
| 异步 | 复用 `TaskQueue` 的 `agent.doc.ingest` | 队列 `off` 时同步解析，语义一致 |

### 8.9 运维与数据自主（S1.16 / BACKLOG B3·B5·B7）

| 关注点 | 做法 | 位置 |
| --- | --- | --- |
| 在途消息回收 | 取用时 `ZADD {prefix}:{topic}:claimed`（score=取用时刻），ack/nack 同步 `ZREM`；巡检按 `TASK_VISIBLE_TIMEOUT_S` 搬回并 `attempt+1` | `app/tasks/redis_queue.py` 的 `receive/ack/nack/sweep`、`app/tasks/worker.py` 的 `_sweep_loop` |
| 巡检开关 | `TASK_SWEEP_INTERVAL_S<=0` 关闭（只保留进程启动时的 `recover`）；默认 60s 扫一次、120s 判超时 | `app/config.py`、`app/api/app.py` |
| 指标 | 进程内累加，`/metrics` 抓取时现渲染；HTTP 用**路由模板**做标签，队列深度抓取时读 | `app/core/metrics.py`、`app/api/observability.py`、`app/runtime/runner.py`、`app/tools/gateway.py` |
| 记忆自主 | 删除（物理）+ 导出（`version/exported_at/facts`）；`user_id` 只来自 token | `app/storage/{base,memory,mysql}.py`、`app/api/routes.py` |
| 语义边界 | 巡检回收是 at-least-once：慢任务可能被执行两次，消费端按 `key`/`event_id` 幂等 | ADR-0009 第 4 条、`tests/test_task_queue.py` |

### 8.10 管理端运维与图谱（S1.17 / BACKLOG B6）

| 关注点 | 做法 | 位置 |
| --- | --- | --- |
| 队列现场 | 只读聚合：逐 topic 取 `depth`/`dead_letters`，worker 取 `processed`/`failed`；`TASK_BACKEND=off` 时返回 `enabled=false` 与空 topic 计数 | `app/api/routes.py` 的 `admin_tasks`、`pet-lumina-web/src/views/agent/Queue.vue` |
| 死信重放 | `limit` 上限 10（前端按死信数取小值），重放后 `attempt=1`；确认框写明"先确认下游已修好" | `RedisTaskQueue.replay_dead_letter`、`Queue.vue` 的 `ElMessageBox.confirm` |
| 管理员删记忆 | `DELETE /agent/admin/memory`，按 `(user_id, pet_id, key)` 物理删除；打 `admin.access`（`scope=memory.delete`），未命中 404 | `app/api/routes.py`、`app/storage/{memory,mysql}.py` |
| 三层图谱 | 只读 Agent 侧数据：`pet:{id or all}` 中心 + `fact:{key}` + `run:{id}`；边为 `remembered` / `happened`；上限事实 50、会话 10、每会话 10 轮 | `app/api/routes.py` 的 `admin_graph`、`pet-lumina-web/src/views/agent/Graph.vue` |
| 权限来源 | 与 6.3/6.4 一致：`role` 来自 Java `/auth/current`（S1.17 给 `LoginUserVO` 补了 `role` 字段），后端模式下忽略请求头 | `app/api/deps.py`、`backend/.../model/vo/LoginUserVO.java` |
| 前端渲染约束 | 节点尺寸由 `data.symbolSize` 给（series 级回调在本版 vue-echarts 下取不到 params，会退化成 0 尺寸只剩标签），`value` 必须有占位值 | `Graph.vue` 注释、S1.17 REPORT 的 D4 |

### 8.11 宠物画像快照（S1.18 / BACKLOG C2）

| 关注点 | 做法 | 位置 |
| --- | --- | --- |
| 定位 | 画像是「事实的当前快照」：`memory_fact` 存原子事实，`profile_snapshot` 存按规则聚合的文档，二者分工明确 | `docs/plans/s1.18-profile.md` §0 |
| 生成方式 | **确定性纯函数**：只读 `confidence >= 0.7` 的事实，同 key 取最高；不调模型，同一批事实重复构建结果一致（除 `meta.builtAt`） | `app/profile/builder.py` 的 `build_profile` |
| 版本 | 追加式：每次重建 `version + 1`，`UNIQUE(user_id, pet_id, version)`，`prune` 保留最近 `PROFILE_KEEP_VERSIONS=20` 版；版本可 diff | `app/storage/{memory,mysql}.py`、`backend/sql/v2.17-profile.sql` |
| 触发 | 挂在记忆消费之后（同一 consumer 内 `should_refresh` → `rebuild`），不与记忆写入并发；去抖 `PROFILE_REFRESH_TTL_S=300` | `app/tasks/consumers.py`、`app/profile/service.py` |
| 过期语义 | 快照写 `meta.factWatermark`；事实的最大 `update_time` 更大即 `stale=true`，前端必须显式提示而不是静默展示旧值 | `ProfileService.is_stale`、`Profile.vue` |
| 对话注入 | 只注入「风险 / 待办」两行，不把整份画像塞进 system（控制 token，也避免模型复述内部结构） | `app/graph/nodes.py` 的 `prepare_node` |
| 可追溯 | `evidence` 每条带 `factId`；删事实后重建，结论随之消失 | `Profile.vue` 证据表、S1.18 REPORT D1 |

### 8.12 退避重试、多副本与桌宠（S1.19 / BACKLOG B4·B2·C6）

| 关注点 | 做法 | 位置 |
| --- | --- | --- |
| 失败退避 | `nack` 写 `{prefix}:{topic}:retry` ZSET（score=到期时刻），`backoff = min(base·2^(attempt-1), cap)`；巡检 `retry_due` 到期搬回，`attempt + 1` | `app/tasks/{base,inprocess,redis_queue}.py`、`TaskWorker._sweep_loop` |
| 死信重投 | **默认关闭**（`TASK_DLQ_REDRIVE_INTERVAL_S=0`）；打开后按周期挑最早死信，`redrives + 1`，达 `TASK_DLQ_MAX_REDRIVES` 就留在死信等人处理 | `redrive_dead_letters`、`test_redrive_dead_letters_respects_max_redrives` |
| 为什么退避 | 下游抖动时立刻重投会变成热循环，把一次故障放大成雪崩；指数退避 + 上限把压力摊平 | `docs/plans/s1.19-b4-b2-deskpet.md` §1 |
| 多副本一致性 | 队列/事件/限流/幂等都在 Redis 或 MySQL 里共享；**熔断是进程内状态**，多副本各自熔断（已知限制，写进 SPEC 6.10） | `scripts/multi_replica_smoke`（8/8） |
| 桌宠（档 A / v2） | H5 + 分层 SVG 角色（7 个 `data-part`：tail/body/arms/head/hair/ears/eyes）；状态由**真实字段**推导（健康分/步数/喂食进度/未读提醒/时段），纯函数 `derivePetMood` 可单测；**部件级 CSS 动画 + 视线跟随 + 拖拽 + 单击爱心**（`petMotion` 纯函数）；可关闭、尊重 `prefers-reduced-motion` | `src/utils/petMood.ts`、`src/utils/petMotion.ts`、`src/components/pet/ChibiPet.vue`、`src/components/pet/DeskPet.vue` |
| 桌宠不做什么 | 不编造「亲密度」、不随机、不做语音；台词只在本地位图 + i18n 文案，不额外调模型 | `petMood.spec.ts`(10)、`petMotion.spec.ts`(7)、`DeskPet.spec.ts`(5) |

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
| 可追溯 | `agent.admin` 只读接口 + `admin.access` 审计 | `test_admin.py`（9 例）+ `scripts.admin_smoke`（6/6）+ 浏览器实测 |
| 不重复计费 | 用户维度幂等键 + 回放 | `test_idempotency.py`（4 例）+ `scripts.idempotency_smoke`（8/8，真 MySQL/Redis） |
| 故障隔离 | 熔断 + `503` 快速失败 + 探针降级 | `test_circuit.py`（8 例）+ 真机 `/readyz` 四项 check |
| 不雪崩 | 失败指数退避 + 死信有界重投（默认关） | `test_task_queue.py`（B4 三条）+ `scripts.multi_replica_smoke`（8/8） |
| 多副本可扩 | 队列/事件/限流/幂等共享存储，熔断标注为单实例限制 | `scripts.multi_replica_smoke`（8/8） |

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
