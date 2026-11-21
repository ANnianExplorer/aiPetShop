/**
 * Agent 错误码 → 界面文案。
 *
 * 契约（docs/spec/agent-runtime-api.md §4.3.1）：
 * - `code` 是稳定标识，客户端按它映射三语文案；
 * - `message` 是中文兜底，只在「客户端不认识这个 code」时展示给用户；
 * - `detail.retry_after_s` 存在时，把「稍后再试」升级成「N 秒后再试」。
 *
 * 这里只返回 `{ key, params }`，不依赖 i18n 实例：
 * 映射表可以被单测穷举，组件只负责用 `t(key, params)` 渲染。
 */

export interface AgentErrorLabel {
  /** i18n key，例如 `agentError.rateLimitedWithRetry` */
  key: string
  /** 插值参数，目前只有 `{ seconds }` */
  params?: Record<string, number>
}

/** 后端 `app/core/errors.py` 里 ErrorCode 的稳定值 */
const CODE_KEYS: Readonly<Record<string, string>> = Object.freeze({
  invalid_request: 'agentError.invalidRequest',
  invalid_arguments: 'agentError.invalidArguments',
  unauthorized: 'agentError.unauthorized',
  forbidden: 'agentError.forbidden',
  not_found: 'agentError.notFound',
  tool_not_allowed: 'agentError.toolNotAllowed',
  tool_failed: 'agentError.toolFailed',
  backend_error: 'agentError.backendError',
  model_error: 'agentError.modelError',
  model_not_configured: 'agentError.modelNotConfigured',
  run_timeout: 'agentError.runTimeout',
  budget_exceeded: 'agentError.budgetExceeded',
  rate_limited: 'agentError.rateLimited',
  circuit_open: 'agentError.circuitOpen',
})

/** 带 `retry_after_s` 时用「N 秒后再试」的版本 */
const RETRY_KEYS: Readonly<Record<string, string>> = Object.freeze({
  rate_limited: 'agentError.rateLimitedWithRetry',
  http_429: 'agentError.rateLimitedWithRetry',
  circuit_open: 'agentError.circuitOpenWithRetry',
})

/** 客户端自己造的码（网络层 / 流中断），同样走本地化 */
const CLIENT_KEYS: Readonly<Record<string, string>> = Object.freeze({
  network: 'agentError.network',
  empty_stream: 'agentError.streamInterrupted',
})

const HTTP_KEYS: Readonly<Record<number, string>> = Object.freeze({
  401: 'agentError.unauthorized',
  403: 'agentError.forbidden',
  404: 'agentError.notFound',
  408: 'agentError.network',
  429: 'agentError.rateLimited',
  500: 'agentError.serverError',
  502: 'agentError.serverError',
  503: 'agentError.serverError',
  504: 'agentError.serverError',
})

/** 非正数 / NaN 都视为「没有可靠的等待时间」，退回普通文案 */
function retrySeconds(value: number | undefined): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return null
  return Math.ceil(value)
}

function httpKey(code: string): string | null {
  const matched = /^http_(\d{3})$/.exec(code)
  if (!matched) return null
  const status = Number(matched[1])
  const exact = HTTP_KEYS[status]
  if (exact) return exact
  if (status >= 500 && status <= 599) return 'agentError.serverError'
  return null
}

/**
 * 把错误码映射成文案 key。
 *
 * @param code 稳定错误码（SSE `error.code` / `AgentRequestError.code`）
 * @param retryAfterS 后端建议的重试等待秒数（`detail.retry_after_s` 或 `Retry-After`）
 * @returns 文案 key；`null` 表示客户端不认识，调用方应回退服务端 `message`
 */
export function agentErrorLabel(code: string | undefined, retryAfterS?: number): AgentErrorLabel | null {
  if (!code) return null

  const seconds = retrySeconds(retryAfterS)
  if (seconds !== null && RETRY_KEYS[code]) {
    return { key: RETRY_KEYS[code], params: { seconds } }
  }

  const key = CODE_KEYS[code] ?? CLIENT_KEYS[code] ?? httpKey(code)
  return key ? { key } : null
}

/** 组件传进来的 `t`：只要求「key + 数字插值」这一种能力，避免耦合 vue-i18n 类型 */
export type AgentErrorTranslator = (key: string, params?: Record<string, number>) => string

/**
 * 组件侧唯一入口：
 * 已知 code → 三语；未知 code → 服务端 message；两者都没有 → 通用文案。
 */
export function translateAgentError(
  t: AgentErrorTranslator,
  code: string | undefined,
  message: string | undefined,
  retryAfterS?: number,
): string {
  const label = agentErrorLabel(code, retryAfterS)
  if (label) return label.params ? t(label.key, label.params) : t(label.key)
  const fallback = message?.trim() ?? ''
  return fallback !== '' ? fallback : t('agentError.unknown')
}
