/**
 * Pet-Agent 前后端契约（与 `backend-agent/app/runtime/runner.py` 的事件结构一一对应）。
 *
 * 注意：所有 id 都是**字符串**。后端 `core/ids.py` 生成 19 位雪花号，
 * 直接当 number 用会丢精度（项目里已有 BigInt 兜底的先例）。
 */

export type AgentRoute = 'L1' | 'L2' | 'L3'

export interface AgentCitation {
  kind: string
  id: string
  label: string
  locator?: string
}

export interface AgentUsage {
  prompt_tokens: number
  completion_tokens: number
}

export interface AgentStep {
  seq: number
  kind: string
  name?: string | null
  status: string
  latency_ms?: number
  error?: string | null
}

export interface RouteEvent {
  session_id: string
  run_id: string
  route: AgentRoute
  intent: string
  reason?: string
}

export interface ToolEvent {
  name: string
  status: string
  latency_ms?: number
}

export interface DeltaEvent {
  text: string
}

export interface DoneEvent {
  run_id: string
  session_id: string
  message_id: string
  route: AgentRoute
  intent: string
  answer: string
  citations: AgentCitation[]
  steps: AgentStep[]
  usage: AgentUsage
  latency_ms: number
}

export interface ErrorEvent {
  code: string
  message: string
  retryable: boolean
}

/** 会话消息（GET /agent/sessions/{id}/messages） */
export interface AgentMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  run_id?: string | null
  citations: AgentCitation[]
  create_time?: string | null
}

/** 会话摘要（GET /agent/sessions）：不含 user_id，本来就是自己的 */
export interface AgentSessionItem {
  id: string
  pet_id?: string | null
  channel: string
  title: string
  message_count: number
  create_time?: string | null
}

export interface AgentSessionPage {
  total: number
  items: AgentSessionItem[]
}

/** 上传到知识库的文档（status: 0 排队 / 1 解析中 / 2 就绪 / 3 失败 / 4 不支持） */
export interface AgentDocument {
  id: string
  name: string
  mime: string
  size_bytes: number
  status: number
  status_label: string
  chunk_count: number
  error?: string | null
}

/** 聊天面板里的一条气泡（比后端 Message 多了流式状态） */
export interface ChatBubble {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations: AgentCitation[]
  /** 正在流式生成 */
  streaming?: boolean
  /** 本条消息走过的工具（用于展示"正在查健康数据"） */
  tools: ToolEvent[]
  error?: string
}
