/**
 * 对话页错误文案（S1.36 / BACKLOG D8）。
 *
 * 验证「服务端稳定 code → 本地化文案」这条链路，覆盖：
 * SSE error、HTTP 429、未知 code 回退、空 message 兜底。
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import enUS from '@/locales/en-US.json'
import { AgentRequestError, fetchSessionMessages, fetchSessions } from '@/api/agent'
import { streamChatResilient } from '@/utils/resilientChat'
import type { AgentEvent } from '@/api/agent'
import ChatView from './ChatView.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ back: vi.fn(), push: vi.fn() }),
}))

vi.mock('@/api/agent', async importOriginal => {
  const actual = await importOriginal<typeof import('@/api/agent')>()
  return {
    ...actual,
    fetchSessionMessages: vi.fn(),
    fetchSessions: vi.fn(),
    uploadDocument: vi.fn(),
  }
})

vi.mock('@/utils/resilientChat', () => ({
  streamChatResilient: vi.fn(),
}))

vi.mock('@/pet/signal', () => ({
  publishWorkState: vi.fn(),
}))

interface FakeStream {
  handlers: { onEvent: (event: AgentEvent) => void } | null
  finish: () => void
}

function controlStream(): FakeStream {
  const state: FakeStream = { handlers: null, finish: () => {} }
  vi.mocked(streamChatResilient).mockImplementation(async (_payload, hooks) => {
    state.handlers = hooks
    await new Promise<void>(resolve => {
      state.finish = resolve
    })
    return { resumes: 0, lastEventId: 1, finished: true }
  })
  return state
}

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const i18n = createI18n({ legacy: false, locale: 'en-US', messages: { 'en-US': enUS } })
  return mount(ChatView, {
    attachTo: document.body,
    global: { plugins: [pinia, i18n] },
  })
}

async function sendMessage(wrapper: ReturnType<typeof mountView>, text = 'hello') {
  await wrapper.get('[data-testid="chat-input"]').setValue(text)
  await wrapper.get('[data-testid="chat-send"]').trigger('click')
  await flushPromises()
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  vi.mocked(fetchSessionMessages).mockResolvedValue([])
  vi.mocked(fetchSessions).mockResolvedValue({ total: 0, items: [] })
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('ChatView 错误文案本地化', () => {
  it('SSE rate_limited + retry_after_s：英文文案带秒数，不出现服务端中文', async () => {
    const stream = controlStream()
    const wrapper = mountView()
    await flushPromises()

    await sendMessage(wrapper)
    stream.handlers?.onEvent({
      event: 'error',
      data: {
        code: 'rate_limited',
        message: '请求太频繁，请稍后再试',
        retryable: true,
        detail: { retry_after_s: 37 },
      },
    })
    await flushPromises()

    const error = wrapper.get('[data-testid="chat-error"]')
    expect(error.text()).toContain('Too many requests. Try again in 37 seconds.')
    expect(error.text()).not.toContain('请求太频繁')

    stream.finish()
    await flushPromises()
    wrapper.unmount()
  })

  it('未知 code 回退服务端 message，不把错误吞成通用文案', async () => {
    const stream = controlStream()
    const wrapper = mountView()
    await flushPromises()

    await sendMessage(wrapper)
    stream.handlers?.onEvent({
      event: 'error',
      data: { code: 'future_code', message: '新的服务端提示', retryable: false },
    })
    await flushPromises()

    expect(wrapper.get('[data-testid="chat-error"]').text()).toContain('新的服务端提示')

    stream.finish()
    await flushPromises()
    wrapper.unmount()
  })

  it('未知 code 且 message 为空时展示通用文案', async () => {
    const stream = controlStream()
    const wrapper = mountView()
    await flushPromises()

    await sendMessage(wrapper)
    stream.handlers?.onEvent({
      event: 'error',
      data: { code: 'future_code', message: '', retryable: false },
    })
    await flushPromises()

    expect(wrapper.get('[data-testid="chat-error"]').text()).toContain(
      'Something went wrong. Try again later.',
    )

    stream.finish()
    await flushPromises()
    wrapper.unmount()
  })

  it('HTTP 429 带 detail.retry_after_s 时同样本地化', async () => {
    vi.mocked(streamChatResilient).mockRejectedValue(
      new AgentRequestError('请求太频繁', 'http_429', true, { retry_after_s: 12 }),
    )
    const wrapper = mountView()
    await flushPromises()

    await sendMessage(wrapper)

    const error = wrapper.get('[data-testid="chat-error"]')
    expect(error.text()).toContain('Too many requests. Try again in 12 seconds.')
    expect(error.text()).not.toContain('请求太频繁')

    wrapper.unmount()
  })
})
