/**
 * 断线自动重连：一次对话 = 一条 run，连接只是它的「读者」。
 *
 * 服务端（S1.23）已经把 run 的生命周期从 HTTP 连接里拆出来了：连接断了，run 照样跑完，
 * 事件照样按 seq 落进日志。所以客户端断线后**不需要重发消息**（重发会撞上幂等键，
 * 或者干脆开启第二次执行），只要拿着 run_id + 已收到的最大 id 去 `/events?follow=1`
 * 接着读就行——接上以后是同一份日志，既不会漏，也不会重复渲染。
 *
 * 三层行为：
 * 1. 正常：open 一次，事件直达；
 * 2. 中途断了但有 run_id：按 `[3000, 3000, 6000]` 的间隔重连，最多三次，
 *    每次 `after` 都是「已渲染的最大 id」，期间通过 onLink 告诉界面「正在重连（第 N 次）」；
 * 3. 连 route 都没拿到，或三次都失败 / 收到终态 error：抛给调用方，走原来的「重试」按钮。
 *
 * 依赖注入（open / replay / sleep）是为了让重连节奏能被单测精确控制，不在测试里真等 9 秒。
 */

import {
  AgentRequestError,
  isDoneEvent,
  isErrorEvent,
  isRouteEvent,
  replayRun,
  streamChat,
  type AgentEvent,
  type ChatPayload,
} from '@/api/agent'

/** `live` 正常；`reconnecting` 正在重连（attempt 从 1 开始）；`resumed` 刚接上 */
export type LinkState = 'live' | 'reconnecting' | 'resumed'

export interface ReconnectHooks {
  onEvent: (event: AgentEvent) => void
  /** 链路状态变化：界面据此显示「正在重连（第 2 次）」而不是干等 */
  onLink?: (state: LinkState, attempt: number, delayMs: number) => void
}

export interface ReconnectOptions {
  /** 取消信号：用户离开页面 / 点停止时立即中断重连，不留下悬挂的定时器 */
  signal?: AbortSignal
  /** 每次重连前的等待；长度即最大重连次数 */
  retryDelaysMs?: readonly number[]
  sleep?: (delayMs: number, signal?: AbortSignal) => Promise<void>
  open?: (payload: ChatPayload, onEvent: ReconnectHooks['onEvent'], signal?: AbortSignal) => Promise<void>
  replay?: (
    runId: string,
    after: number,
    onEvent: ReconnectHooks['onEvent'],
    signal?: AbortSignal,
  ) => Promise<void>
}

export interface StreamOutcome {
  /** 实际重连成功了几次 */
  resumes: number
  /** 已经消费到的最大事件 id，下次续传从这里接 */
  lastEventId: number
  /** 服务端是否给出了终态（done / error） */
  finished: boolean
}

const DEFAULT_DELAYS = [3000, 3000, 6000] as const

function abortError(): Error {
  const error = new Error('aborted')
  error.name = 'AbortError'
  return error
}

function isAbort(error: unknown): boolean {
  return (error as Error | null)?.name === 'AbortError'
}

/** 可以重连的错误：网络抖动、5xx、流被中间层提前掐断；401/404/校验错误重试也没用 */
function isRetryable(error: unknown): boolean {
  if (error instanceof AgentRequestError) return error.retryable
  return true
}

function defaultSleep(delayMs: number, signal?: AbortSignal): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(abortError())
      return
    }
    const onAbort = () => {
      clearTimeout(timer)
      reject(abortError())
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, delayMs)
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

/**
 * 发起一次对话，断线自动续上。
 * 返回时说明「这一轮真的结束了（或重连次数用完）」。
 */
export async function streamChatResilient(
  payload: ChatPayload,
  hooks: ReconnectHooks,
  options: ReconnectOptions = {},
): Promise<StreamOutcome> {
  const delays = options.retryDelaysMs ?? DEFAULT_DELAYS
  const sleep = options.sleep ?? defaultSleep
  const open = options.open ?? ((body, onEvent, signal) => streamChat(body, { signal, onEvent }))
  const replay =
    options.replay ??
    ((runId, after, onEvent, signal) => replayRun(runId, after, { signal, onEvent }))

  const signal = options.signal
  let cursor = 0
  let runId: string | null = null
  let finished = false

  const onEvent: ReconnectHooks['onEvent'] = (event) => {
    if (typeof event.id === 'number') {
      if (event.id <= cursor) return // 续传边界重合：渲染过的不再追加
      cursor = event.id
    }
    if (runId === null && isRouteEvent(event.data)) runId = event.data.run_id
    if ((event.event === 'done' && isDoneEvent(event.data)) || (event.event === 'error' && isErrorEvent(event.data))) {
      finished = true
    }
    hooks.onEvent(event)
  }

  hooks.onLink?.('live', 0, 0)
  let lastError: unknown = null
  try {
    await open(payload, onEvent, signal)
  } catch (error) {
    if (isAbort(error)) throw error
    // 401/404/参数错误：重连也是同一个结果，直接交给界面（401 要跳登录）
    if (!isRetryable(error)) throw error
    // 连 route 都没拿到就没有游标可续：这不是「断线」，是压根没连上
    if (!runId) throw error
    lastError = error
  }

  let attempt = 0
  let resumes = 0
  while (!finished) {
    if (attempt >= delays.length) {
      throw lastError instanceof Error ? lastError : new Error('重连多次仍未接上，请稍后再试')
    }
    if (!runId) throw lastError ?? new Error('这条消息没有对应的运行记录，无法续传')

    const delayMs = delays[attempt]
    hooks.onLink?.('reconnecting', attempt + 1, delayMs)
    await sleep(delayMs, signal)

    attempt += 1
    try {
      await replay(runId, cursor, onEvent, signal)
      resumes += 1
      if (!finished) hooks.onLink?.('live', 0, 0)
    } catch (error) {
      if (isAbort(error)) throw error
      if (!isRetryable(error)) throw error
      lastError = error
    }
  }

  return { resumes, lastEventId: cursor, finished }
}
