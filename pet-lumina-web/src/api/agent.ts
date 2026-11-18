/**
 * Agent 管理端接口：走独立的 axios 实例。
 *
 * 为什么不复用 `request.ts`：那边绑定的是 Java 业务后端的 `{code,data,message}` 信封，
 * 而 Agent 运行时是纯 REST（直接返回资源对象、用 HTTP 状态码表达错误）。
 * 硬塞进同一个拦截器会让 403/404 被当成"业务码异常"，错误信息也拿不到。
 */
import axios from 'axios'

const baseURL = (import.meta.env.VITE_AGENT_BASE_URL || 'http://localhost:8099').replace(/\/+$/, '')

const agent = axios.create({ baseURL, timeout: 20000 })

agent.interceptors.request.use((config) => {
  const token = localStorage.getItem('satoken')
  if (token) {
    config.headers['satoken'] = token
  }
  return config
})

export class AgentApiError extends Error {
  code: string
  status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'AgentApiError'
    this.code = code
    this.status = status
  }
}

agent.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status: number = error.response?.status ?? 0
    const body = error.response?.data ?? {}
    const message =
      typeof body?.message === 'string'
        ? body.message
        : status === 403
          ? '当前账号没有管理员权限'
          : status === 0
            ? 'Agent 服务不可达'
            : 'Agent 服务返回异常'
    return Promise.reject(new AgentApiError(message, body?.code || 'unknown', status))
  },
)

export interface AdminModelConfig {
  provider: string
  base_url: string
  model: string
  enabled: boolean
  source: 'db' | 'env' | 'none'
  has_api_key: boolean
  api_key_masked: string
  updated_by: string | null
  update_time: string | null
  fallback: 'env' | 'none'
  runtime_model: string | null
  runtime_source: 'db' | 'env' | 'none'
  error: string | null
}

export interface AdminModelConfigPayload {
  provider: string
  base_url: string
  model: string
  api_key: string
  enabled: boolean
}

export interface AdminModelConfigTestResult {
  ok: boolean
  latency_ms: number
  model: string
  provider: string
}

export interface AdminSessionItem {
  id: string
  user_id: string
  pet_id: string | null
  channel: string
  title: string
  message_count: number
  create_time: string | null
}

export interface AdminSessionList {
  total: number
  page: number
  page_size: number
  items: AdminSessionItem[]
}

export interface AdminMessage {
  id: string
  role: string
  content: string
  run_id: string | null
  citations: { kind: string; id: string; label: string; locator: string }[]
  create_time: string | null
}

export interface AdminStep {
  seq: number
  kind: string
  name: string
  status: string
  latency_ms: number
  error: string | null
}

export interface AdminRun {
  id: string
  route: string
  intent: string
  status: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  latency_ms: number
  error: string | null
  steps: AdminStep[]
}

export interface AdminSessionDetail {
  session: AdminSessionItem
  messages: AdminMessage[]
  runs: AdminRun[]
}

export interface AdminDayUsage {
  day: string
  runs: number
  tokens: number
}

export interface AdminUsage {
  days: number
  runs: number
  users: number
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  avg_latency_ms: number
  by_day: AdminDayUsage[]
}

export interface AdminMemoryFact {
  id: string
  key: string
  label: string
  value: string
  confidence: number
  update_time: string | null
}

export interface AdminMemory {
  pet_id: string | null
  facts: AdminMemoryFact[]
}

export interface AdminTaskTopic {
  topic: string
  depth: number
  dead_letters: number
}

export interface AdminTasks {
  enabled: boolean
  backend: string
  processed: number
  failed: number
  topics: AdminTaskTopic[]
}

export interface GraphNode {
  id: string
  kind: 'pet' | 'fact' | 'event'
  label: string
  detail: string | null
}

export interface GraphEdge {
  source: string
  target: string
  kind: string
  label: string | null
}

export interface AdminGraph {
  user_id: string
  pet_id: string | null
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export function getAdminModelConfig(): Promise<AdminModelConfig> {
  return agent.get('/agent/admin/model-config')
}

export function saveAdminModelConfig(
  payload: AdminModelConfigPayload,
): Promise<AdminModelConfig> {
  return agent.put('/agent/admin/model-config', payload)
}

export function testAdminModelConfig(
  payload: AdminModelConfigPayload,
): Promise<AdminModelConfigTestResult> {
  return agent.post('/agent/admin/model-config/test', payload)
}

export function listAdminSessions(params: {
  page: number
  page_size: number
  user_id?: string
  q?: string
}): Promise<AdminSessionList> {
  return agent.get('/agent/admin/sessions', { params })
}

export function getAdminSessionDetail(sessionId: string): Promise<AdminSessionDetail> {
  return agent.get(`/agent/admin/sessions/${encodeURIComponent(sessionId)}`)
}

export function getAdminUsage(days = 7): Promise<AdminUsage> {
  return agent.get('/agent/admin/usage', { params: { days } })
}

export function getAdminMemory(userId: string, petId?: string | null): Promise<AdminMemory> {
  return agent.get('/agent/admin/memory', {
    params: { user_id: userId, ...(petId ? { pet_id: petId } : {}) },
  })
}

export function deleteAdminMemory(params: {
  userId: string
  key: string
  petId?: string | null
}): Promise<{ deleted: boolean; key: string }> {
  return agent.delete('/agent/admin/memory', {
    params: {
      user_id: params.userId,
      key: params.key,
      ...(params.petId ? { pet_id: params.petId } : {}),
    },
  })
}

export function getAdminTasks(): Promise<AdminTasks> {
  return agent.get('/agent/admin/tasks')
}

export function replayDeadLetter(
  topic: string,
  limit = 10,
): Promise<{ topic: string; replayed: number }> {
  return agent.post('/agent/admin/tasks/dead-letters/replay', { topic, limit })
}

export function getAdminGraph(params: {
  userId: string
  petId?: string | null
  sessions?: number
  runsPerSession?: number
}): Promise<AdminGraph> {
  return agent.get('/agent/admin/graph', {
    params: {
      user_id: params.userId,
      ...(params.petId ? { pet_id: params.petId } : {}),
      sessions: params.sessions ?? 3,
      runs_per_session: params.runsPerSession ?? 3,
    },
  })
}

export interface AdminProfileEvidence {
  key: string
  value: string
  confidence: number
  factId?: string
}

export interface AdminProfileDoc {
  basics?: Record<string, unknown>
  traits?: Record<string, unknown>
  preferences?: Array<{ text: string }>
  riskFlags?: Array<{ text: string }>
  careGaps?: Array<{ text: string }>
  evidence?: AdminProfileEvidence[]
  meta?: { factWatermark?: string; builtAt?: string }
}

export interface AdminProfile {
  id: string
  user_id: string | null
  pet_id: string | null
  version: number
  fact_count: number
  confidence: number
  create_time: string | null
  stale: boolean
  data: AdminProfileDoc
}

export interface AdminProfileVersionList {
  total: number
  items: AdminProfile[]
}

export function getAdminProfile(params: {
  userId: string
  petId?: string | null
}): Promise<AdminProfile> {
  return agent.get('/agent/admin/profile', {
    params: {
      user_id: params.userId,
      ...(params.petId ? { pet_id: params.petId } : {}),
    },
  })
}

export function getAdminProfileVersions(params: {
  userId: string
  petId?: string | null
  limit?: number
}): Promise<AdminProfileVersionList> {
  return agent.get('/agent/admin/profile/versions', {
    params: {
      user_id: params.userId,
      ...(params.petId ? { pet_id: params.petId } : {}),
      limit: params.limit ?? 10,
    },
  })
}

export default agent
