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
| `app/runtime/` | `eventlog`/`runner` | 事件可续传；run 终态不可改 |
| `app/api/` | `deps`/`schemas`/`routes`/`app`/`observability` | 依赖全部注入，测试不需要真模型/真库 |
| `app/core/` | `errors`/`ids`/`logging` | 错误模型、19 位雪花 id、单行 JSON 日志 |
| `tests/` | 契约级单测 | 59 项，不依赖网络/MySQL/密钥 |
| `evals/` | 评测用例 + 阈值 runner | 23 条用例，不过阈值就退出码非 0 |

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
.venv\Scripts\python -m pytest        # 59 passed
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
mysql -u root -p < backend/sql/v2.10-agent.sql
# .env: PET_AGENT_REPO_BACKEND=mysql
#       PET_AGENT_MYSQL_DSN=mysql://root:密码@localhost:3306/petlumina
```

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

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/healthz` | 进程存活：repo 模式、模型是否配置、工具清单、图是否构建成功 |
| GET | `/readyz` | 能否接流量：存储 `SELECT 1` + 模型已配置；否则 503（不回堆栈） |
| POST | `/agent/chat` | SSE；头 `satoken`（或 `Authorization: Bearer`），body `{message, session_id?, pet_id?, channel?}` |
| GET | `/agent/runs/{run_id}/events` | 断线续传；支持 `?after=N` 与 `Last-Event-ID` |
| GET | `/agent/sessions/{id}/messages` | 历史消息（App 进聊天页） |

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
- `pytest` → 59 项：路由、网关六道防线、存储契约（内存/MySQL 同一套断言）、图（L1/L2/hop 上限/坏参数）、API（SSE 事件序列、续传三种方式等价、越权、失败收敛）、可观测（request_id/日志字段/readyz 降级）。
- `python -m evals.run` → 三套件、阈值硬卡：`routing ≥ 95%`、`safety = 100%`、`memory = 100%`。
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
