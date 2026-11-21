import { describe, expect, it } from 'vitest'
import { applyAgentEvent, historyToBubbles } from './chatStream'
import type { ChatBubble } from '@/types/agent'

function bubble(overrides: Partial<ChatBubble> = {}): ChatBubble {
  return {
    id: 'assistant-1',
    role: 'assistant',
    content: '',
    citations: [],
    tools: [],
    streaming: true,
    ...overrides,
  }
}

describe('applyAgentEvent', () => {
  it('route 事件只回传会话 id，不碰内容', () => {
    const target = bubble()
    const outcome = applyAgentEvent(target, {
      event: 'route',
      data: { run_id: 'r1', session_id: 's1', route: 'L2', intent: 'health' },
    })
    expect(outcome.sessionId).toBe('s1')
    expect(target.content).toBe('')
    expect(target.streaming).toBe(true)
  })

  it('tool 事件追加到气泡工具列表', () => {
    const target = bubble()
    applyAgentEvent(target, {
      event: 'tool',
      data: { name: 'search_logs', status: 'ok', latency_ms: 12 },
    })
    applyAgentEvent(target, {
      event: 'tool',
      data: { name: 'get_health_summary', status: 'ok', latency_ms: 8 },
    })
    expect(target.tools.map((tool) => tool.name)).toEqual(['search_logs', 'get_health_summary'])
  })

  it('delta 事件按到达顺序累加文本', () => {
    const target = bubble()
    for (const text of ['上次', '疫苗', '是 9 月 1 日']) {
      applyAgentEvent(target, { event: 'delta', data: { text } })
    }
    expect(target.content).toBe('上次疫苗是 9 月 1 日')
  })

  it('done 事件用服务端答案覆盖，并落地引用、结束流式', () => {
    const target = bubble({ content: '半截答案' })
    const outcome = applyAgentEvent(target, {
      event: 'done',
      data: {
        run_id: 'r1',
        session_id: 's1',
        answer: '完整答案',
        citations: [{ kind: 'log', id: '7001', label: '疫苗记录' }],
      },
    })
    expect(target.content).toBe('完整答案')
    expect(target.streaming).toBe(false)
    expect(target.citations).toEqual([{ kind: 'log', id: '7001', label: '疫苗记录' }])
    expect(outcome.sessionId).toBe('s1')
  })

  it('done 事件没有 citations 时给空数组（模板里可直接 v-for）', () => {
    const target = bubble()
    applyAgentEvent(target, {
      event: 'done',
      data: { run_id: 'r1', session_id: 's1', answer: '好' },
    })
    expect(target.citations).toEqual([])
  })

  it('error 事件在没有任何输出时标记丢弃气泡', () => {
    const target = bubble()
    const outcome = applyAgentEvent(target, {
      event: 'error',
      data: { code: 'model_error', message: '模型超时' },
    })
    expect(outcome.error).toBe('模型超时')
    expect(outcome.dropBubble).toBe(true)
    expect(target.streaming).toBe(false)
  })

  it('已经输出过内容的 error 不丢气泡，保留半截答案给用户看', () => {
    const target = bubble({ content: '已经说了一半' })
    const outcome = applyAgentEvent(target, {
      event: 'error',
      data: { code: 'run_timeout', message: '超时' },
    })
    expect(outcome.dropBubble).toBe(false)
    expect(target.content).toBe('已经说了一半')
  })

  it('error 事件透出错误码与重试秒数，供界面按 code 本地化', () => {
    const target = bubble()
    const outcome = applyAgentEvent(target, {
      event: 'error',
      data: {
        code: 'rate_limited',
        message: '请求太频繁',
        retryable: true,
        detail: { retry_after_s: 2.5 },
      },
    })
    expect(outcome.error).toBe('请求太频繁')
    expect(outcome.errorCode).toBe('rate_limited')
    expect(outcome.retryAfterS).toBe(2.5)
  })

  it('error 事件没有 detail 或秒数非法时，不带 retryAfterS', () => {
    const target = bubble()
    const noDetail = applyAgentEvent(target, {
      event: 'error',
      data: { code: 'circuit_open', message: '熔断', retryable: true },
    })
    expect(noDetail.retryAfterS).toBeUndefined()

    const badDetail = applyAgentEvent(target, {
      event: 'error',
      data: {
        code: 'circuit_open',
        message: '熔断',
        retryable: true,
        detail: { retry_after_s: Number.NaN },
      },
    })
    expect(badDetail.retryAfterS).toBeUndefined()
  })

  it('未知事件与格式不符的数据都被忽略，不抛异常', () => {
    const target = bubble()
    expect(applyAgentEvent(target, { event: 'ping', data: null })).toEqual({})
    expect(applyAgentEvent(target, { event: 'delta', data: { text: 1 } })).toEqual({})
    expect(target.content).toBe('')
  })

  it('delta 缺 text 字段时不把 undefined 拼进字符串', () => {
    const target = bubble({ content: 'a' })
    applyAgentEvent(target, { event: 'delta', data: { foo: 'bar' } })
    expect(target.content).toBe('a')
  })
})

describe('historyToBubbles', () => {
  it('只保留 user/assistant 且不回溯工具痕迹', () => {
    const bubbles = historyToBubbles([
      { id: '1', role: 'user', content: '你好' },
      { id: '2', role: 'tool', content: '{"ok":true}' },
      { id: '3', role: 'assistant', content: '在呢', citations: [{ kind: 'log', id: '1', label: 'x' }] },
    ])
    expect(bubbles.map((item) => item.id)).toEqual(['1', '3'])
    expect(bubbles[1].citations).toHaveLength(1)
    expect(bubbles[1].tools).toEqual([])
  })
})
