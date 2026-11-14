import { describe, expect, it, vi } from 'vitest'
import { streamChatResilient } from './resilientChat'
import { AgentRequestError } from '@/api/agent'
import type { AgentEvent } from '@/api/agent'

function routeEvent(id: number, runId = 'run-1'): AgentEvent {
  return {
    id,
    event: 'route',
    data: { run_id: runId, session_id: 'sess-1', route: 'L2', intent: 'health' },
  }
}

function deltaEvent(id: number, text: string): AgentEvent {
  return { id, event: 'delta', data: { text } }
}

function doneEvent(id: number, answer: string): AgentEvent {
  return { id, event: 'done', data: { answer, run_id: 'run-1', session_id: 'sess-1' } }
}

function collector() {
  const events: AgentEvent[] = []
  return { events, onEvent: (event: AgentEvent) => events.push(event) }
}

const payload = { message: '上次疫苗是什么时候' }

/** 不真的等待，但记录重连节奏——测试要能断言「3 秒、3 秒、6 秒」 */
function quietSleep() {
  return vi.fn(async (_delayMs: number, _signal?: AbortSignal) => {})
}

describe('streamChatResilient', () => {
  it('正常一轮：事件原样透传，不触发重连', async () => {
    const { events, onEvent } = collector()
    const sleep = quietSleep()
    const open = vi.fn(async (_payload: unknown, emit: (e: AgentEvent) => void) => {
      emit(routeEvent(1))
      emit(deltaEvent(2, '上次'))
      emit(doneEvent(3, '上次疫苗是 9 月 1 日'))
    })
    const links: string[] = []

    const outcome = await streamChatResilient(
      payload,
      { onEvent, onLink: (state) => links.push(state) },
      { open, sleep, replay: vi.fn() },
    )

    expect(events.map((e) => e.id)).toEqual([1, 2, 3])
    expect(outcome).toEqual({ resumes: 0, lastEventId: 3, finished: true })
    expect(sleep).not.toHaveBeenCalled()
    expect(links).toEqual(['live'])
  })

  it('中途断线：拿 run_id + 已收 id 续上，事件不重不漏', async () => {
    const { events, onEvent } = collector()
    const sleep = quietSleep()
    const open = vi.fn(async (_payload: unknown, emit: (e: AgentEvent) => void) => {
      emit(routeEvent(1))
      emit(deltaEvent(2, '前半'))
      throw new AgentRequestError('网络断了', 'network')
    })
    const replay = vi.fn(async (_runId: string, after: number, emit: (e: AgentEvent) => void) => {
      expect(after).toBe(2)
      // 服务端从 after 之后返回；这里故意多给一条已渲染过的，验证前端去重
      emit(deltaEvent(2, '前半'))
      emit(deltaEvent(3, '后半'))
      emit(doneEvent(4, '前半后半'))
    })
    const links: Array<[string, number]> = []

    const outcome = await streamChatResilient(
      payload,
      { onEvent, onLink: (state, attempt) => links.push([state, attempt]) },
      { open, replay, sleep },
    )

    expect(events.map((e) => e.id)).toEqual([1, 2, 3, 4])
    const text = events
      .filter((e) => e.event === 'delta')
      .map((e) => String((e.data as { text: string }).text))
      .join('')
    expect(text).toBe('前半后半')
    expect(outcome).toEqual({ resumes: 1, lastEventId: 4, finished: true })
    expect(sleep).toHaveBeenCalledTimes(1)
    expect(sleep).toHaveBeenCalledWith(3000, undefined)
    expect(links).toEqual([
      ['live', 0],
      ['reconnecting', 1],
    ])
  })

  it('流被中间层「干净地」掐断（没报错也没 done）也会续上', async () => {
    const { events, onEvent } = collector()
    const sleep = quietSleep()
    const open = vi.fn(async (_payload: unknown, emit: (e: AgentEvent) => void) => {
      emit(routeEvent(1))
    })
    const replay = vi.fn(async (_runId: string, after: number, emit: (e: AgentEvent) => void) => {
      expect(after).toBe(1)
      emit(doneEvent(2, '你好呀'))
    })

    const outcome = await streamChatResilient(payload, { onEvent }, { open, replay, sleep })

    expect(events.map((e) => e.id)).toEqual([1, 2])
    expect(outcome.finished).toBe(true)
  })

  it('每次重连都从「已收最大 id」接着要，不会重播开头', async () => {
    const { onEvent } = collector()
    const afters: number[] = []
    const sleep = quietSleep()
    const open = vi.fn(async (_payload: unknown, emit: (e: AgentEvent) => void) => {
      emit(routeEvent(1))
      emit(deltaEvent(2, '一'))
      throw new AgentRequestError('断了', 'network')
    })
    const replay = vi.fn(async (_runId: string, after: number, emit: (e: AgentEvent) => void) => {
      afters.push(after)
      if (afters.length === 1) {
        emit(deltaEvent(3, '二'))
        throw new AgentRequestError('又断了', 'network')
      }
      emit(deltaEvent(4, '三'))
      emit(doneEvent(5, '一二三'))
    })

    const outcome = await streamChatResilient(payload, { onEvent }, { open, replay, sleep })

    expect(afters).toEqual([2, 3])
    expect(outcome.lastEventId).toBe(5)
    expect(sleep.mock.calls.map((call) => call[0])).toEqual([3000, 3000])
  })

  it('三次都失败就把错误抛给界面，走「重试」按钮', async () => {
    const { onEvent } = collector()
    const sleep = quietSleep()
    const open = vi.fn(async (_payload: unknown, emit: (e: AgentEvent) => void) => {
      emit(routeEvent(1))
      throw new AgentRequestError('断了', 'network')
    })
    const replay = vi.fn(async () => {
      throw new AgentRequestError('还是连不上', 'network')
    })

    await expect(
      streamChatResilient(payload, { onEvent }, { open, replay, sleep }),
    ).rejects.toThrow('还是连不上')
    expect(sleep.mock.calls.map((call) => call[0])).toEqual([3000, 3000, 6000])
    expect(replay).toHaveBeenCalledTimes(3)
  })

  it('连 route 都没拿到（没有 run_id）就不做无意义的重连', async () => {
    const { onEvent } = collector()
    const sleep = quietSleep()
    const open = vi.fn(async () => {
      throw new AgentRequestError('连不上智能体服务', 'network')
    })
    const replay = vi.fn()

    await expect(
      streamChatResilient(payload, { onEvent }, { open, replay, sleep }),
    ).rejects.toThrow('连不上智能体服务')
    expect(sleep).not.toHaveBeenCalled()
    expect(replay).not.toHaveBeenCalled()
  })

  it('不可重试的错误（404/401）立即抛出，不浪费时间重连', async () => {
    const { onEvent } = collector()
    const sleep = quietSleep()
    const open = vi.fn(async (_payload: unknown, emit: (e: AgentEvent) => void) => {
      emit(routeEvent(1))
      throw new AgentRequestError('运行不存在', 'not_found', false)
    })
    const replay = vi.fn()

    await expect(
      streamChatResilient(payload, { onEvent }, { open, replay, sleep }),
    ).rejects.toThrow('运行不存在')
    expect(replay).not.toHaveBeenCalled()
  })

  it('abort 之后立刻停下，不再重连', async () => {
    const { onEvent } = collector()
    const controller = new AbortController()
    const sleep = vi.fn(async () => {
      controller.abort()
      const error = new Error('aborted')
      error.name = 'AbortError'
      throw error
    })
    const open = vi.fn(async (_payload: unknown, emit: (e: AgentEvent) => void) => {
      emit(routeEvent(1))
      throw new AgentRequestError('断了', 'network')
    })
    const replay = vi.fn()

    await expect(
      streamChatResilient(
        payload,
        { onEvent },
        { open, replay, sleep, signal: controller.signal },
      ),
    ).rejects.toMatchObject({ name: 'AbortError' })
    expect(replay).not.toHaveBeenCalled()
  })
})
