# ADR-0007 可观测性基线：JSON 日志 + request_id + 就绪探针，不引入 APM

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）
- 计划：[s1.6-production-hardening.md](../plans/s1.6-production-hardening.md) P0

## 背景

上线前必须回答三个问题：**谁调用的、慢在哪、花了多少**。
当前只有 uvicorn 默认文本日志，`run_id / tool / 耗时 / token` 全在数据库里，出问题时要把日志和 SQL 手动对齐，且多进程交错后无法区分请求。

可选：接 OpenTelemetry / Datadog / Langfuse 之类的 APM。

## 选项

| 选项 | 收益 | 代价 |
| --- | --- | --- |
| A. 直接上 OTel + Collector | 全链路追踪，行业标准 | 多一套基础设施；SDK 侵入运行时；本阶段没有 trace 后端可看 |
| B. JSON stdout 日志 + request_id 关联（本决定） | 零额外设施，容器化后直接可采集；字段可查询 | 没有自动埋点，跨服务追踪靠 id 串联 |
| C. 什么都不做，只查数据库 | 无成本 | 线上排障只能靠复现；成本维度无法归因 |

## 决定

采用 **B**：
1. `app/core/logging.py` 输出单行 JSON：`ts / level / logger / msg / request_id / user_id / run_id / tool / latency_ms / tokens`；
2. `RequestContextMiddleware` 生成或透传 `x-request-id`，并随响应头回写，客户端可凭它报障；
3. `contextvars` 携带 `request_id`，业务日志不用层层传参；
4. 日志**只记 id、长度、耗时、错误码，不记消息原文**（隐私）；
5. 探针分离：`/healthz` 只证明进程活着，`/readyz` 检查存储与模型是否可用，K8s 两类探针各取其一。

## 后果

**变好**：一条 `grep '"run_id":"1794..."'` 就能拿到该 run 的全部事件；成本字段可与 `agent_run` 表对账；隐私风险可控。

**变差**：没有分布式追踪，跨 `App → Runtime → Java` 只能靠 `request_id`/`satoken` 手串；JSON 日志比文本大一倍。

**过渡路径**：字段名按 OTel 语义命名（`http.request.method` 之类暂不强行对齐），P2 若接 Collector 只需替换 formatter/追加 exporter，业务代码不动。

## 验证方式

- `pytest tests/test_observability.py`：日志行可 `json.loads`、含 `request_id`、响应头带 `x-request-id`、`/readyz` 在 repo 不可用时返回 503；
- e2e：`scripts/e2e_smoke.py` 继续 10/10，说明日志改造未破坏协议。
