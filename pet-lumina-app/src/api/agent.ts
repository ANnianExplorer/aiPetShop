/**
 * Pet-Agent 客户端：SSE 对话流 + 断线续传 + 历史回读。
 *
 * 约定：
 * - 身份用 `satoken` 请求头（与 `/api/v1` 一致），不把用户 ID 放在请求体里；
 * - 所有事件都带 `id`，中途断线可以用 `after=<最后一条 id>` 续传，不会重复渲染；
 * - 网络层错误与业务错误分开：前者抛 `AgentRequestError('network')`，后者带后端 code。
 */

import { SseDecoder, type SseMessage } from './sse'
import type {
  AgentDocument,
  AgentMemoryExport,
  AgentMemoryFact,
  AgentMessage,
  AgentSessionPage,
  DoneEvent,
  ErrorEvent,
  DeltaEvent,
  RouteEvent,
  ToolEvent,
} from '@/types/agent'

export class AgentRequestError extends Error {
  readonly code: string
  readonly retryable: boolean

  constructor(message: string, code = 'network', retryable = true) {
    super(message)
    this.name = 'AgentRequestError'
    this.code = code
    this.retryable = retryable
  }
}

export type AgentEventName = 'route' | 'tool' | 'delta' | 'done' | 'error' | string

export interface AgentEvent {
  id?: number
  event: AgentEventName
  data: unknown
}

export interface StreamHandlers {
  onEvent: (event: AgentEvent) => void
}

export interface ChatPayload {
  message: string
  sessionId?: string | null
  petId?: string | null
  channel?: 'app' | 'web' | 'internal'
}

/** 服务地址：同一域名的反代走相对路径，本地开发用 VITE_AGENT_BASE_URL 指向 8099 */
export function agentBaseUrl(): string {
  const configured = (import.meta.env.VITE_AGENT_BASE_URL as string | undefined) ?? ''
  return configured.replace(/\/+$/, '')
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('satoken')
  return token ? { satoken: token } : {}
}

async function assertOk(response: Response): Promise<void> {
  if (response.ok) {
    return
  }
  let code = `http_${response.status}`
  let message = `请求失败（${response.status}）`
  try {
    const payload = (await response.json()) as { code?: string; message?: string }
    if (payload.code) code = payload.code
    if (payload.message) message = payload.message
  } catch {
    // 非 JSON 错误体：保留状态码提示即可
  }
  throw new AgentRequestError(message, code, response.status >= 500)
}

/** 逐块读取响应体，交给 SseDecoder 解析；每拿到一条完整记录就回调。 */
async function pump(response: Response, onEvent: StreamHandlers['onEvent']): Promise<void> {
  if (!response.body) {
    throw new AgentRequestError('服务未返回流式响应', 'empty_stream', true)
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  const sse = new SseDecoder()

  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      for (const message of sse.push(decoder.decode(value, { stream: true }))) {
        emit(message, onEvent)
      }
    }
    for (const message of sse.push(decoder.decode())) {
      emit(message, onEvent)
    }
    for (const message of sse.flush()) {
      emit(message, onEvent)
    }
  } finally {
    reader.releaseLock()
  }
}

function emit(message: SseMessage, onEvent: StreamHandlers['onEvent']): void {
  let data: unknown = null
  try {
    data = JSON.parse(message.data)
  } catch {
    data = message.data
  }
  onEvent({ id: message.id, event: message.event, data })
}

/** 发起一次对话，事件通过 onEvent 增量回调；返回时说明流已结束。 */
export async function streamChat(
  payload: ChatPayload,
  handlers: StreamHandlers & { signal?: AbortSignal },
): Promise<void> {
  const body: Record<string, string> = { message: payload.message }
  if (payload.sessionId) body.session_id = payload.sessionId
  if (payload.petId) body.pet_id = payload.petId
  body.channel = payload.channel ?? 'app'

  let response: Response
  try {
    response = await fetch(`${agentBaseUrl()}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...authHeaders(),
      },
      body: JSON.stringify(body),
      signal: handlers.signal,
    })
  } catch (error) {
    if ((error as Error).name === 'AbortError') throw error
    throw new AgentRequestError('连不上智能体服务，请确认后端已启动', 'network')
  }

  await assertOk(response)
  await pump(response, handlers.onEvent)
}

/** 断线续传：拉取某个 run 在 after 之后的事件（等价于重新订阅）。 */
export async function replayRun(
  runId: string,
  after: number,
  handlers: StreamHandlers & { signal?: AbortSignal },
): Promise<void> {
  const response = await fetch(
    `${agentBaseUrl()}/agent/runs/${encodeURIComponent(runId)}/events?after=${after}`,
    { headers: { Accept: 'text/event-stream', ...authHeaders() }, signal: handlers.signal },
  )
  await assertOk(response)
  await pump(response, handlers.onEvent)
}

/** 历史消息（进入聊天页时拉一次） */
export async function fetchSessionMessages(sessionId: string): Promise<AgentMessage[]> {
  const response = await fetch(
    `${agentBaseUrl()}/agent/sessions/${encodeURIComponent(sessionId)}/messages`,
    { headers: { Accept: 'application/json', ...authHeaders() } },
  )
  await assertOk(response)
  const payload = (await response.json()) as { messages?: AgentMessage[] }
  return payload.messages ?? []
}

/** 会话列表：服务端按最后活跃时间倒序，只返回本人的会话。 */
export async function fetchSessions(page = 1, pageSize = 20): Promise<AgentSessionPage> {
  const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  const response = await fetch(`${agentBaseUrl()}/agent/sessions?${query}`, {
    headers: { Accept: 'application/json', ...authHeaders() },
  })
  await assertOk(response)
  const payload = (await response.json()) as AgentSessionPage
  return { total: payload.total ?? 0, items: payload.items ?? [] }
}

// ---- 文档上传（A3 文档问答） ----

export async function uploadDocument(file: File, petId: string | null = null): Promise<AgentDocument> {
  const form = new FormData()
  form.append('file', file)
  if (petId) form.append('pet_id', petId)
  const response = await fetch(`${agentBaseUrl()}/agent/documents`, {
    method: 'POST',
    headers: authHeaders(), // 不手写 Content-Type：交给浏览器带 boundary
    body: form,
  })
  await assertOk(response)
  return (await response.json()) as AgentDocument
}

// ---- 长期记忆（B7：用户可查看 / 删除 / 导出） ----
//
// 契约（docs/spec/agent-runtime-api.md 6.1）：
// `pet_id` 为空表示「不带宠物维度」的事实，不是「全部事实」；
// 想看全部必须对「通用 + 每只宠物」各拉一次，合并规则见 utils/memoryScope.ts。

function memoryQuery(petId: string | null, extra: Record<string, string> = {}): string {
  const query = new URLSearchParams(extra)
  if (petId) query.set('pet_id', petId)
  return query.toString()
}

/** 某范围的记忆事实；limit 契约上限 50。 */
export async function fetchMemoryFacts(
  petId: string | null = null,
  limit = 50,
): Promise<AgentMemoryFact[]> {
  const query = memoryQuery(petId, { limit: String(limit) })
  const response = await fetch(`${agentBaseUrl()}/agent/memory/me?${query}`, {
    headers: { Accept: 'application/json', ...authHeaders() },
  })
  await assertOk(response)
  const payload = (await response.json()) as { facts?: AgentMemoryFact[] }
  return payload.facts ?? []
}

/** 删除一条记忆；key 不存在时后端 404（code=not_found），由调用方展示错误。 */
export async function deleteMemoryFact(
  key: string,
  petId: string | null = null,
): Promise<void> {
  const query = memoryQuery(petId, { key })
  const response = await fetch(`${agentBaseUrl()}/agent/memory/me?${query}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json', ...authHeaders() },
  })
  await assertOk(response)
}

/** 某范围的全量导出（后端内部 limit=200，不受列表 50 条限制）。 */
export async function exportMemory(petId: string | null = null): Promise<AgentMemoryExport> {
  const query = memoryQuery(petId)
  const suffix = query ? `?${query}` : ''
  const response = await fetch(`${agentBaseUrl()}/agent/memory/me/export${suffix}`, {
    headers: { Accept: 'application/json', ...authHeaders() },
  })
  await assertOk(response)
  return (await response.json()) as AgentMemoryExport
}

// ---- 事件载荷收窄：保持 UI 层不写宽泛断言 ----

export function isRouteEvent(data: unknown): data is RouteEvent {
  return typeof data === 'object' && data !== null && 'run_id' in data && 'route' in data
}

export function isToolEvent(data: unknown): data is ToolEvent {
  return typeof data === 'object' && data !== null && 'name' in data && 'status' in data
}

export function isDeltaEvent(data: unknown): data is DeltaEvent {
  return typeof data === 'object' && data !== null && typeof (data as DeltaEvent).text === 'string'
}

export function isDoneEvent(data: unknown): data is DoneEvent {
  return typeof data === 'object' && data !== null && 'answer' in data && 'run_id' in data
}

export function isErrorEvent(data: unknown): data is ErrorEvent {
  return typeof data === 'object' && data !== null && 'code' in data && 'message' in data
}
