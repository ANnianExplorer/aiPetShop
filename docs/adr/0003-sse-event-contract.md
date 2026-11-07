# ADR-0003 对外用五种事件 + `id:` 游标的 SSE 契约

- 状态：Accepted
- 日期：2026-11-07
- 决策人：架构（本仓）
- 规格：[spec/agent-runtime-api.md](../spec/agent-runtime-api.md)

## 背景

对话必须"边说边出字"，且要能被前端稳定消费、断线后不重复计费。候选方案：WebSocket、SSE、长轮询。

约束：App 是 H5（浏览器 + 将来的 HBuilder 打包），只需要服务端单向推送；需要与 HTTP 鉴权头共存；需要断点续传。

## 选项

| 选项 | 成本 | 风险 |
| --- | --- | --- |
| WebSocket | 双向、低延迟 | 连接管理/心跳/重连/多副本共享状态复杂；本项目没有双向需求 |
| 长轮询 | 兼容性最好 | 首字延迟高、连接空转、实现反而更绕 |
| SSE（本决定） | 单向推送、复用 HTTP 鉴权、天然文本 | 浏览器原生 `EventSource` 不能带自定义头、不能 POST body、续传只能重连同 URL |

## 决定

用 **SSE**，并自定义五种事件：`route` / `tool` / `delta` / `done` / `error`，每条事件带 `id:` 递增游标。
前端不用 `EventSource`，改 `fetch + ReadableStream`（见 ADR-0006）。

## 后果

**变好**：
- 一条流里既有"过程"（route/tool）又有"结果"（done），前端可做工具 chip、引用、可解释性；
- `id:` 游标让 `Last-Event-ID` / `?after=N` 续传成为一行代码；
- `done.answer` 是权威全文，客户端可用它纠正流式拼接误差。

**变差**：
- 事件类型一旦公开就是契约，新增类型要向后兼容（前端必须忽略未知事件，已实现）；
- 事件只缓存在进程内存（`capacity=512`、`ttl=900s`），多副本/长断线需要 Redis 广播——列为 S2 前置。

## 验证方式

- `test_api.py`：事件序列、`id` 连续、三种续传等价；
- `scripts/e2e_smoke.py`：`full=8 after=6 resume=6`；
- 前端 `sse.spec.ts`：跨 chunk、多行 data、CRLF、`flush` 残片。
