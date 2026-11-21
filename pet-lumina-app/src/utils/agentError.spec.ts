import { describe, expect, it } from 'vitest'
import enUS from '@/locales/en-US.json'
import jaJP from '@/locales/ja-JP.json'
import zhCN from '@/locales/zh-CN.json'
import { agentErrorLabel } from './agentError'

/** 与 backend-agent/app/core/errors.py 的 ErrorCode 保持同步 */
const AGENT_CODES = [
  'invalid_request',
  'invalid_arguments',
  'unauthorized',
  'forbidden',
  'not_found',
  'tool_not_allowed',
  'tool_failed',
  'backend_error',
  'model_error',
  'model_not_configured',
  'run_timeout',
  'budget_exceeded',
  'rate_limited',
  'circuit_open',
] as const

function keyPaths(value: unknown, prefix = ''): string[] {
  if (typeof value !== 'object' || value === null) return [prefix]
  const record = value as Record<string, unknown>
  return Object.entries(record).flatMap(([key, child]) =>
    keyPaths(child, prefix ? `${prefix}.${key}` : key),
  )
}

function lookup(messages: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>((node, part) => {
    if (typeof node !== 'object' || node === null) return undefined
    return (node as Record<string, unknown>)[part]
  }, messages)
}

describe('agentErrorLabel', () => {
  it('后端每个稳定错误码都有文案映射', () => {
    for (const code of AGENT_CODES) {
      const label = agentErrorLabel(code)
      expect(label?.key, code).toMatch(/^agentError\./)
    }
  })

  it('映射出来的 key 在三语里都存在且非空字符串', () => {
    const labels = [
      ...AGENT_CODES.map(code => agentErrorLabel(code)),
      agentErrorLabel('network'),
      agentErrorLabel('empty_stream'),
      agentErrorLabel('http_401'),
      agentErrorLabel('http_403'),
      agentErrorLabel('http_404'),
      agentErrorLabel('http_429'),
      agentErrorLabel('http_500'),
      agentErrorLabel('http_599'),
      agentErrorLabel('rate_limited', 37),
      agentErrorLabel('circuit_open', 5),
      agentErrorLabel('http_429', 12),
    ]
    for (const label of labels) {
      expect(label).not.toBeNull()
      for (const messages of [zhCN, enUS, jaJP]) {
        const text = lookup(messages, label?.key ?? '')
        expect(typeof text, label?.key).toBe('string')
        expect((text as string).length, label?.key).toBeGreaterThan(0)
      }
    }
  })

  it('HTTP 状态码按语义归类，未知 4xx 留给服务端 message', () => {
    expect(agentErrorLabel('http_401')?.key).toBe('agentError.unauthorized')
    expect(agentErrorLabel('http_403')?.key).toBe('agentError.forbidden')
    expect(agentErrorLabel('http_404')?.key).toBe('agentError.notFound')
    expect(agentErrorLabel('http_408')?.key).toBe('agentError.network')
    expect(agentErrorLabel('http_429')?.key).toBe('agentError.rateLimited')
    expect(agentErrorLabel('http_500')?.key).toBe('agentError.serverError')
    expect(agentErrorLabel('http_503')?.key).toBe('agentError.serverError')
    expect(agentErrorLabel('http_599')?.key).toBe('agentError.serverError')
    expect(agentErrorLabel('http_418')).toBeNull()
  })

  it('客户端网络码与流中断码也走本地化', () => {
    expect(agentErrorLabel('network')?.key).toBe('agentError.network')
    expect(agentErrorLabel('empty_stream')?.key).toBe('agentError.streamInterrupted')
  })

  it('有可靠 retry_after_s 时展示「N 秒后再试」，并向上取整', () => {
    expect(agentErrorLabel('rate_limited', 37)).toEqual({
      key: 'agentError.rateLimitedWithRetry',
      params: { seconds: 37 },
    })
    expect(agentErrorLabel('rate_limited', 0.4)).toEqual({
      key: 'agentError.rateLimitedWithRetry',
      params: { seconds: 1 },
    })
    expect(agentErrorLabel('circuit_open', 5)).toEqual({
      key: 'agentError.circuitOpenWithRetry',
      params: { seconds: 5 },
    })
    expect(agentErrorLabel('http_429', 12)).toEqual({
      key: 'agentError.rateLimitedWithRetry',
      params: { seconds: 12 },
    })
  })

  it('retry_after_s 缺失或不可靠时退回普通文案', () => {
    for (const seconds of [undefined, 0, -3, Number.NaN, Number.POSITIVE_INFINITY]) {
      expect(agentErrorLabel('rate_limited', seconds)).toEqual({ key: 'agentError.rateLimited' })
      expect(agentErrorLabel('circuit_open', seconds)).toEqual({ key: 'agentError.circuitOpen' })
    }
  })

  it('未知 / 空错误码返回 null，由调用方回退服务端 message', () => {
    expect(agentErrorLabel('future_code')).toBeNull()
    expect(agentErrorLabel('')).toBeNull()
    expect(agentErrorLabel(undefined)).toBeNull()
  })

  it('三语 locale 的 agentError 键集合完全一致（防止漏翻）', () => {
    const zhKeys = keyPaths(zhCN.agentError)
    expect(keyPaths(enUS.agentError)).toEqual(zhKeys)
    expect(keyPaths(jaJP.agentError)).toEqual(zhKeys)
    expect(zhKeys).toHaveLength(20)
  })
})
