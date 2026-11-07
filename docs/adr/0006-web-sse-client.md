# ADR-0006 前端用 `fetch + ReadableStream` 自研 SSE 客户端

- 状态：Accepted
- 日期：2026-11-07
- 决策人：前端（本仓）
- 规格：[spec/web-chat-ui.md](../spec/web-chat-ui.md)

## 背景

浏览器原生 `EventSource` 有三个硬限制，正好全部撞上本项目的需求：

1. **不能带自定义请求头** —— 我们的凭证是 `satoken` 头，而不是 cookie；
2. **只能 GET** —— 对话需要 POST 一段 `message`，长文本放 query 不合适；
3. **续传只能重连同一 URL** —— 我们要用 `Last-Event-ID` + `?after=N` 精确续传。

另外没有现成的、不引入额外依赖的解析器能同时满足"逐块喂数据"和"可单测"。

## 选项

| 选项 | 收益 | 代价 |
| --- | --- | --- |
| A. 原生 `EventSource` | 零代码 | 三个限制全踩，且 token 只能塞 query（泄漏到日志） |
| B. `@microsoft/fetch-event-source` | 现成重连/退避 | 多一个依赖；其重连语义与我们的 `run_id` 续传不完全一致，改造成本不低于自研 |
| C. `fetch` + `ReadableStream` + 自研解析（本决定） | 完全可控、零依赖、可单测 | 要自己处理分块边界、CRLF、多行 data、`flush` |

## 决定

采用 **C**，拆成两个文件：

- `src/api/sse.ts`：**纯解析器** `SseDecoder.push(chunk) / flush()`，只吃字符串、吐 `{id?, event, data}`，不碰网络；
- `src/api/agent.ts`：传输层，`fetch` + `getReader()` + `TextDecoder('utf-8')`，把 chunk 喂给解析器，异常转 `AgentRequestError(code, retryable)`。

UI 层只消费 `applyAgentEvent(bubble, event)`，不直接碰流。

## 后果

**变好**：能带 `satoken` 头、能 POST body、能精确续传；解析器 10 条单测覆盖跨 chunk/CRLF/多行 data/残片。

**变差**：重连与退避要自己写（当前只在 UI 层做"重试"按钮）；浏览器分块边界问题必须靠测试兜住。

## 验证方式

- `npx vitest run` → 20 passed（`sse.spec.ts` 10 + `chatStream.spec.ts` 10）；
- 浏览器端到端：真实 SSE 流渲染，`done.answer` 覆盖流式拼接结果。
