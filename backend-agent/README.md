# backend-agent · PetLumina Agent Runtime

宠物智能体的**执行引擎层**。不替代 Spring Boot 后端：业务真源（用户/宠物/健康/记录）仍在 Java + MySQL，
本服务只负责「调度 + 工具 + 记忆 + 运行轨迹」，通过用户自己的 `satoken` 调 `/api/v1/*` 取数。
权限边界不复制，也就不存在「Agent 绕过权限」的后门。

```text
App / 管理端 ──SSE──>  api/          传输层：鉴权、请求校验、SSE 编码、错误映射
                       runtime/      编排层：run 生命周期、事件缓冲、超时、用量结算
                       graph/        决策层：route → (L1 直答 | L2 ReAct 工具循环)
                       tools/        能力层：工具契约 + 网关六道防线 + 业务后端客户端
                       storage/      持久层：会话/消息/运行/步骤/审计（memory | mysql）
                       llm/          模型层：OpenAI 兼容 + 可脚本化的假模型
                       domain/       内核：实体、事件、路由规则（不依赖任何框架）
                                   └── 业务真源：Java 后端 /api/v1（透传 satoken）
```

## 为什么这样分层

抄袭的是**分层边界**，不是代码：

| 来源 | 拿走的 | 没拿的 |
| --- | --- | --- |
| deer-flow（SuperAgent harness） | 传输/编排/决策/能力/持久五层切分，每层只能向下依赖 | 沙箱、子代理、消息网关（S1 不需要，也不该提前引入） |
| mem0 | 「记忆是算子不是表」的思路：提取→去重→更新→检索，S2 落到 `memory_fact` | 托管平台与向量库绑定 |
| claw-eval | 用例即数据 + 硬阈值 + 逐条报告，可进 CI | 人类标注流水线 |

依赖方向是一条硬规则：`api → runtime → graph → tools/storage/llm → domain`，
反向 import 一律禁止（domain 不认识 FastAPI，也不认识 MySQL）。改这一条，比改一百行代码更能防止屎山。

## 目录

| 路径 | 职责 | 关键约束 |
| --- | --- | --- |
| `app/domain/` | `models`/`events`/`router` | 纯 Python；路由是**确定性关键词**，不吃模型 |
| `app/llm/` | `base`/`openai_compat`/`fake` | 429/5xx 重试、工具参数坏 JSON 标 `parse_error` 不炸 run |
| `app/tools/` | `spec`/`registry`/`gateway`/`client`/`pet` | schema 由 pydantic 生成；写操作默认不暴露 |
| `app/storage/` | `base`（Protocol）/`memory`/`mysql` | 两套实现共用一份契约测试 |
| `app/graph/` | `state`/`nodes`/`builder` | hop 与调用预算都有硬上限 |
| `app/runtime/` | `eventlog`/`runner` | 事件可续传；run 终态不可改；配额与记忆在这里被编排 |
| `app/api/` | `deps`/`schemas`/`routes`/`app`/`observability` | 依赖全部注入，测试不需要真模型/真库 |
| `app/core/` | `errors`/`ids`/`logging`/`ratelimit`/`circuit`/`redis_client` | 错误模型、19 位雪花 id、单行 JSON 日志、配额、熔断、RESP2 兼容的 Redis 客户端 |
| `app/memory/` | `extract`/`ops`/`service` | 事实抽取（规则）、ADD/UPDATE/NOOP 算子、写入与召回 |
| `app/tasks/` | `base`/`inprocess`/`redis`/`consumers`/`worker` | 旁路任务队列：记忆抽取与审计出请求路径；队列满退回同步 |
| `app/rag/` | `models`/`chunker`/`embedder`/`ocr`/`media`/`parsers`/`service` | 文档问答：解析→切分→嵌入→检索；缺 `tesseract`/`ffmpeg` 时明确降级并给原因 |
| `tests/` | 契约级单测 | 222 项（含真机契约），不依赖网络/密钥 |
| `evals/` | 评测用例 + 阈值 runner | 68 条用例，不过阈值就退出码非 0 |

## 快速开始

```bash
cd backend-agent
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # 精确锁定版本
copy .env.example .env          # 填 PET_AGENT_LLM_API_KEY
.venv\Scripts\python -m uvicorn app.main:app --port 8099
```

验证：

```bash
curl http://localhost:8099/healthz    # 进程活着
curl http://localhost:8099/readyz     # 能接流量（存储+模型都 ok 才是 200）
.venv\Scripts\python -m pytest        # 222 项：不带 DSN 为 221 passed + 1 skipped（跳过的是 MySQL 契约变体）
.venv\Scripts\python -m evals.run     # routing/safety/memory 三套件，硬阈值
.venv\Scripts\ruff.exe check .        # 静态检查
```

容器（多阶段、非 root、带 HEALTHCHECK）：

```bash
docker build -t pet-agent .
docker run -p 8099:8099 -e PET_AGENT_LLM_API_KEY=... pet-agent
```

切 MySQL（S1 默认 `memory`，重启即清空）：

```bash
mysql -u root -p < backend/sql/v2.10-agent.sql      # 会话/消息/运行/步骤/工具审计
mysql -u root -p < backend/sql/v2.11-agent-memory.sql  # 长期记忆两表
mysql -u root -p < backend/sql/v2.12-agent-idempotency.sql  # 幂等键（S1.8 P2）
# .env: PET_AGENT_REPO_BACKEND=mysql
#       PET_AGENT_MYSQL_DSN=mysql://root:密码@localhost:3306/petlumina
```

生产形态建议同时切两处（不改代码）：`PET_AGENT_EVENT_BACKEND=redis`（事件流跨副本续传）、
`PET_AGENT_RATE_LIMIT_BACKEND=redis`（配额多副本共享计数）。

## 配置

全部走 `PET_AGENT_` 前缀（`.env` 或环境变量），默认值偏安全：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `PET_AGENT_ENV` | `dev` | `prod` 时强制配置密钥、禁止 header 认证 |
| `PET_AGENT_LLM_API_KEY` | 空 | 空则 `/agent/chat` 返回 `model_not_configured`，进程不会假死 |
| `PET_AGENT_LLM_BASE_URL` | `https://api.deepseek.com/v1` | OpenAI 兼容端点 |
| `PET_AGENT_AUTH_MODE` | `backend` | `backend`=调 `/auth/current` 换身份；`header` 仅 dev/test |
| `PET_AGENT_BACKEND_BASE_URL` | `http://localhost:8080/api/v1` | Java 业务后端 |
| `PET_AGENT_REPO_BACKEND` | `memory` | `memory` \| `mysql` |
| `PET_AGENT_MYSQL_DSN` | 空 | `mysql://user:pass@host:port/db` |
| `PET_AGENT_MAX_TOOL_HOPS` | `6` | L2 工具循环上限 |
| `PET_AGENT_MAX_TOOL_CALLS_PER_RUN` | `8` | 单次运行的**工具调用总预算**（防死循环烧钱） |
| `PET_AGENT_HISTORY_LIMIT` | `20` | 每次带给模型的历史消息条数 |
| `PET_AGENT_RUN_DEADLINE_S` | `60` | 单次运行墙钟上限，超时落 `RunTimeout` |
| `PET_AGENT_LOG_LEVEL` | `INFO` | 结构化日志级别；CI/本地排障用 `DEBUG` |
| `PET_AGENT_RUN_TOKEN_BUDGET` | `30000` | 单次运行累计 token 上限（0=不限）；超了抛 `budget_exceeded` |
| `PET_AGENT_RATE_LIMIT_ENABLED` | `true` | 每用户配额开关（关掉只影响限流，不影响预算） |
| `PET_AGENT_RATE_LIMIT_PER_MINUTE` | `20` | 每分钟对话次数 |
| `PET_AGENT_RATE_LIMIT_PER_DAY` | `300` | 每日对话次数 |
| `PET_AGENT_RATE_LIMIT_BACKEND` | `memory` | `memory`（单副本）/ `redis`（多副本共享） |
| `PET_AGENT_EVENT_BACKEND` | `memory` | `memory` / `redis`（Redis Stream，跨进程续传） |
| `PET_AGENT_REDIS_URL` | `redis://localhost:6379/0` | 事件流与配额共用（客户端固定 RESP2，兼容 Redis 5） |
| `PET_AGENT_CIRCUIT_THRESHOLD` | `5` | 连续失败多少次打开熔断 |
| `PET_AGENT_CIRCUIT_COOLDOWN_S` | `30` | 熔断冷却期，过后放一个探测请求 |
| `PET_AGENT_TASK_BACKEND` | `off` | `off`（同步）/ `memory`（单进程队列）/ `redis`（多副本队列） |
| `PET_AGENT_TASK_QUEUE_SIZE` | `1000` | 内存队列上限，满了退回同步执行 |
| `PET_AGENT_TASK_MAX_ATTEMPTS` | `3` | 消费失败重试次数，超过进死信 |
| `PET_AGENT_TASK_VISIBLE_TIMEOUT_S` | `120` | 取走后超过这么久还没 ack，就认为消费者死了、搬回队列（`attempt+1`） |
| `PET_AGENT_TASK_SWEEP_INTERVAL_S` | `60` | 巡检间隔；`<=0` 关闭（只保留启动时的 `recover`） |
| `PET_AGENT_TASK_RETRY_BASE_S` | `5` | 失败退避首秒数（`min(base·2^(attempt-1), cap)`） |
| `PET_AGENT_TASK_RETRY_CAP_S` | `600` | 退避上限 |
| `PET_AGENT_TASK_DLQ_REDRIVE_INTERVAL_S` | `0` | 死信自动重投周期；`0` = 关闭（需要显式运维决策） |
| `PET_AGENT_TASK_DLQ_MAX_REDRIVES` | `3` | 同一条消息最多被自动重投几次 |
| `PET_AGENT_TASK_DLQ_REDRIVE_LIMIT` | `5` | 每轮每 topic 最多重投几条 |

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/healthz` | 进程存活：repo 模式、模型是否配置、工具清单、图是否构建成功 |
| GET | `/readyz` | 能否接流量：存储 `SELECT 1` + 模型已配置；否则 503（不回堆栈） |
| POST | `/agent/chat` | SSE；头 `satoken`（或 `Authorization: Bearer`），body `{message, session_id?, pet_id?, channel?, client_message_id?}`；带幂等键时重试会回放而不是重跑 |
| GET | `/agent/runs/{run_id}/events` | 断线续传；支持 `?after=N` 与 `Last-Event-ID` |
| GET | `/agent/sessions` | 我的会话列表（分页、按最后活跃倒序、只含本人）：`{total,page,page_size,items}` |
| GET | `/agent/sessions/{id}/messages` | 历史消息（App 进聊天页） |
| GET | `/agent/memory/me` | 我这个账号（可带 `pet_id`）记住的事实：`{id,key,label,value,confidence,update_time}` |
| DELETE | `/agent/memory/me?key=&pet_id=` | 删除我的一条事实（物理删除）；不存在 404 |
| GET | `/agent/memory/me/export?pet_id=` | 导出我的全部事实：`{version,exported_at,pet_id,facts}` |
| GET | `/metrics` | Prometheus 文本：HTTP 请求数/耗时、run、工具调用、token、队列深度（无鉴权、无用户内容） |
| GET | `/agent/usage/me?days=7` | 用量聚合：`runs / prompt_tokens / completion_tokens / total_tokens / avg_latency_ms` |
| GET | `/agent/admin/sessions?page=&page_size=&user_id=&q=` | **管理员**：全部会话（按最后活跃时间倒序，带 `message_count`） |
| GET | `/agent/admin/sessions/{id}` | **管理员**：会话详情 = 消息 + 每轮 run + 每步 step |
| GET | `/agent/admin/memory?user_id=&pet_id=` | **管理员**：看某个账号记住了什么 |
| GET | `/agent/admin/usage?days=7` | **管理员**：全局用量 + 按天趋势 + 活跃用户数 |
| GET | `/agent/admin/tasks` | **管理员**：队列现场 `{enabled,backend,processed,failed,topics:[{topic,depth,dead_letters}]}` |
| POST | `/agent/admin/tasks/dead-letters/replay` | **管理员**：`{topic,limit}` 把死信放回队列（`attempt` 归零），返回 `{topic,replayed}` |
| GET | `/agent/documents/capabilities` | 能力矩阵：`text/pdf/image/video` 的 `supported`+`reason`、`embedder`、`max_bytes` |
| POST | `/agent/documents` | `multipart`：`file` + 可选 `pet_id`；202 返回记录（`status=0` 排队），去重按 `(user, sha256)` |
| GET | `/agent/documents` | 本人文档列表（`limit` 1–100，倒序） |
| GET/DELETE | `/agent/documents/{id}` | 详情 / 软删（他人 id 一律 404，不泄露存在性） |
| GET | `/agent/profile/me?pet_id=` | 我这个账号的宠物画像：`{version,fact_count,confidence,stale,data}`；从未生成过 404 |
| POST | `/agent/profile/me/refresh?pet_id=` | 强制重算画像（版本 +1） |
| GET | `/agent/admin/profile?user_id=&pet_id=` | **管理员**：他人画像（读操作写 `admin.access`，`scope=profile`） |
| GET | `/agent/admin/profile/versions?user_id=&pet_id=&limit=` | **管理员**：画像版本历史（新→旧，`limit` 1–20） |

管理端权限只认 token 换来的 `role`（来自 Java `/auth/current`），请求头 `x-user-role` 在生产
（`AUTH_MODE=backend`）**一律忽略**；非管理员 `403 forbidden`。每次读他人数据打一条
`admin.access` 日志（`admin_id`/`target_user`/`session_id`），不记正文。管理端刻意只读：
不让管理员代发消息，否则"这句话是谁说的"和记忆归属都会失真。

超配额不建 SSE，直接 `429`：`{code:"rate_limited", detail:{retry_after_s,scope,limit}}` + `Retry-After` 头；
正常对话响应头带 `X-RateLimit-Limit` / `X-RateLimit-Remaining`。

所有响应都带 `x-request-id`（自带则回传，≤64 字符），日志行里同样带这个字段——
一条请求从 `run started` 到 `run finished` 可以用它串起来，不用去猜。

SSE 契约（每个事件都带 `id:`，可直接当游标用）：

```text
event: route   data: {session_id, run_id, route, intent, reason}
event: tool    data: {name, status, latency_ms}      # 前端展示"正在查健康数据"
event: delta   data: {text}                          # 逐 token
event: done    data: {run_id, message_id, answer, citations[], steps[], tokens, latency_ms}
event: error   data: {code, message, retryable}
```

`done.citations[]` 是可点回的来源（`kind` + `id` + `locator`），`steps[]` 是运行轨迹——
管理端会话工作台直接用它回放，不另建一套日志。

## 安全模型

1. **身份来自服务端**：`backend` 模式下不信任客户端自称的 `user_id`，一律拿 token 换；
   缓存键是 token 的 sha256 前 16 位，60 秒过期，不缓存明文。
2. **工具入参是封闭 schema**：`extra="forbid"`，模型无法额外塞 `user_id`/`token`——伪造 ID 直接 `invalid_arguments`。
3. **写操作两段式**：副作用工具默认被 `ToolPolicy` 隐藏；即便放开，也只回 `proposal`，等用户确认后 commit。
4. **预算与超时**：hop 上限 + 每 run 调用总预算 + 墙钟 deadline，三把闸分别防死循环、防刷、防挂死。
5. **审计不留原文**：`tool_call_log` 只存入参 digest 与耗时，敏感内容不落库。

## 测试与评测

- `ruff check .` → 静态检查（配置在 `pyproject.toml`，CI 第一道门）。
- `pytest` → 222 项（设 `PET_AGENT_TEST_MYSQL_DSN` 时含真机 MySQL 契约；不带 DSN 为 221 通过 + 1 跳过）：路由、网关六道防线、存储契约（内存/MySQL 同一套断言）、图（L1/L2/hop 上限/坏参数）、API（SSE 事件序列、续传三种方式等价、越权、失败收敛、429 与配额头、记忆注入与用量聚合）、配额（分钟/日窗口、用户隔离、Redis fail-open、`Retry-After`）、事件存储（两实现同契约：序号、游标、裁剪、坏数据跳过）、记忆（抽取规则、ADD/UPDATE/NOOP、隔离、低置信度过滤、导出与删除）、会话列表（本人隔离、最后活跃排序、分页 total）、文档 RAG（切分/嵌入确定性/多编码解析/PDF 分页/OCR 缺失降级/去重与软删复活/检索隔离/删除后不可检索）、可观测（request_id/日志字段/readyz 降级/指标模板与不含用户内容）、管理端（403/401、列表筛选、详情含 steps、审计不含正文、伪造 header 无效、删记忆审计、三层图谱、他人画像与审计）、画像（确定性构建、斤换 kg、低置信度忽略、疫苗过期进 careGaps、版本递增与裁剪、事实更新后 stale）、幂等（同 key 只执行一次、并发唯一键、非法 key 422）、熔断（三态迁移、half_open 单探测、401 不误熔断、readyz 联动）、队列（启动补偿、死信重放、可见性超时巡检）。
- `python -m evals.run` → 三套件、阈值硬卡：`routing ≥ 95%`、`safety = 100%`、`memory ≥ 90%`（现 48/48）。
  用例在 `evals/cases.jsonl`，加一行就是加一条回归；`memory` 支持 `text`（抽取全等）/`observe`（服务层）/`turns`（落库完整性）三种形状；报告落 `evals/reports/latest.json`。
  用例在 `evals/cases.jsonl`，加一行就是加一条回归；报告落 `evals/reports/latest.json`。
- 三者都不需要真模型：`ScriptedModel` 把模型的输出变成脚本，测的是**我们的编排**，不是模型的智商。
- CI：`.github/workflows/agent-ci.yml` 依次跑 ruff → pytest → evals → `docker build`，任一红则不入主线。

### 真进程冒烟（唯一能证明"SSE 真的能连"的那一层）

单测跑在 ASGI 内存里，抓不到真实网络下的坑（比如图里少一条边导致上下文为空）。冒烟要三个进程：

```bash
.venv\Scripts\python -m uvicorn tests.stub_java:app --port 8097   # 假 Java 后端
.venv\Scripts\python -m uvicorn tests.stub_llm:app  --port 8098   # 假 LLM（会按提示词真的发 tool_call）
# 再起 app.main:app --port 8099，env 指向上两个
.venv\Scripts\python -m scripts.e2e_smoke
```

10 项检查：healthz、L1 事件序列、L2 真的调用 `search_logs`、citation 指回记录 7001、用量已结算、
续传三方式等价、会话回读、越权读他人会话 404。

P1 专项（配额/用量/记忆，用独立账号 `token-7007`，限流放最后一步）：

```bash
.venv\Scripts\python -m scripts.p1_smoke   # 9/9
```

检查：记忆初始为空 → 说一句「它叫 Lumina，对牛奶过敏」→ 接口里能查到 `allergy=牛奶`（含标签与置信度）→
重复同一句话不产生第二条 → 用量按账号聚合 → 打满配额后 `429 + Retry-After`。

管理端专项（普通用户 403 / 造一条会话 / 管理员列表与详情 / 全局用量 / 无 token 401）：

```bash
.venv\Scripts\python -m scripts.admin_smoke   # 6/6
```

幂等专项（同 key 重试只执行一次 / 消息不翻倍 / 事件可回放 / 非法 key 422）：

```bash
.venv\Scripts\python -m scripts.idempotency_smoke   # 8/8
```

队列运维专项（现场可见 / 死信重放 / 重放后消费清空）：

```bash
.venv\Scripts\python -m scripts.tasks_smoke   # 8/8（需 TASK_BACKEND=redis）
```

文档问答专项（上传 → 解析 → 检索 → 对话引用 → 删除）：

```bash
.venv\Scripts\python -m scripts.migrate_doc_rag   # 建 doc_file / doc_chunk（DSN 从环境变量读）
.venv\Scripts\python -m scripts.rag_smoke        # 10/10
```

运维与数据自主专项（指标 / 记忆导出删除 / 在途消息巡检）：

```bash
.venv\Scripts\python -m scripts.ops_smoke        # 11/11（建议 TASK_SWEEP_INTERVAL_S=2、TASK_VISIBLE_TIMEOUT_S=1）
```

多副本专项（两个 Agent 实例共享 MySQL + Redis，例如 8099 与 8100）：

```bash
.venv\Scripts\python -m scripts.multi_replica_smoke   # 8/8（跨副本事件回放/幂等/不重复消费/记忆/限流）
```

> 该脚本走**真 Java 登录**（`AUTH_MODE=backend` + `BACKEND_BASE_URL` 指向 8080），
> 其余冒烟脚本用桩身份 `token-*`，需要 `BACKEND_BASE_URL` 指向 8097（`tests/stub_java.py`）。

> 真机形态跑法：`REPO_BACKEND=mysql`、`EVENT_BACKEND=redis`、`RATE_LIMIT_BACKEND=redis`、
> `TASK_BACKEND=redis`，八个冒烟全部可跑（10/9/6/8/8/10/11/8）。Redis 5 不支持 RESP3，客户端已固定 `protocol=2`。
> 崩溃恢复：进程启动时先把 `:processing` 里的在途消息搬回队列再开消费，日志 `task inflight recovered on startup`；
> 运行期卡死的消息由巡检按 `TASK_VISIBLE_TIMEOUT_S` 回收，日志 `task inflight swept`；
> 失败消息先进 `:retry` ZSET 按指数退避，日志 `task retry scheduled`（含 `delay_s`），到期由巡检搬回。

真实模型专项（必须有 key，验证"不是本地桩"）：

```bash
$env:PET_AGENT_LLM_API_KEY = "<key>"; $env:PET_AGENT_LLM_BASE_URL = "https://api.deepseek.com/v1"
$env:PET_AGENT_LLM_MODEL = "deepseek-chat"
.venv\Scripts\python -m scripts.real_model_smoke --rounds 3   # 13/13
```

它量的是三件只有真模型才暴露的事：L1 首 token 延迟（P50/P95）、L2 是否真的调了 `search_logs`、
`done.usage` 的 token 与库里的 `agent_run` 是否一致。key 只从环境变量读，不落仓库。

## 记忆是怎么工作的

```text
用户说"它对牛奶过敏"
   → extract.py：正则抽到 {allergy: 牛奶}，置信度 0.95
   → ops.py：内存里没有 → ADD
   → repository.upsert_memory_fact()：唯一键 (user, pet, key) 兜底，重复说不会多一条
下一轮提问
   → recall_lines()：过滤 < 0.7 的猜测 → ["过敏：牛奶"]
   → prepare_node 把它拼进 system 提示（不伪造 user 消息）
   → 召回/写入抛异常就吞掉，本轮照常回答（记忆是增强，不是单点故障）
```

`GET /agent/memory/me` 把这层变可核对——抽取错了能看见、能修，而不是等模型胡说才发现。

## 加一个工具（五步，缺一不可）

1. `app/tools/` 里写 handler + 参数模型（`extra="forbid"`，别放 `user_id`/`token`）；
2. `build_registry()` 里 `register(ToolSpec(...))`，标 `tags` 与 `side_effect`；
3. 若需要新后端端点，先确认它在 Java 侧存在且带 `@AuthCheck`——**不新造权限**；
4. `tests/test_gateway.py` 补一条「该拒的能拒」；`evals/cases.jsonl` 补一条安全或用例；
5. 跑 `pytest -q && python -m evals.run`，两条都绿才算完。

## 已知边界（S1 刻意不做）

- 无向量检索/RAG：`doc_file`/`doc_chunk` 在 S2；
- 无写操作落地：proposal 协议已就位，commit 端点在 S2；
- 无长期记忆：`memory_fact` 在 S2，当前只带最近 `history_limit` 条；
- checkpointer 未接：`build_graph(checkpointer=...)` 留了口子，S2 接 Redis/Postgres 做 interrupt-resume；
- 未做限流与多租户配额：当前假设前面有网关。
