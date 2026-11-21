/**
 * 对话页无障碍基线（S1.35 / BACKLOG D9）。
 *
 * 只验证 DOM 层面的可感知性与焦点闭环：真实读屏软件（NVDA/VoiceOver）的朗读
 * 无法在 jsdom 里自动化，报告里如实写明「未做读屏人工验收」。
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN.json'
import { fetchSessionMessages, fetchSessions } from '@/api/agent'
import { streamChatResilient } from '@/utils/resilientChat'
import type { AgentEvent } from '@/api/agent'
import type { AgentSessionItem } from '@/types/agent'
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

/** 可控的流：先拿到 onEvent 手动喂事件，再放行让 send() 收尾 */
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

const doneEvent: AgentEvent = {
  event: 'done',
  data: {
    run_id: 'r1',
    session_id: 's1',
    message_id: 'm1',
    route: 'L1',
    intent: 'chat',
    answer: '豆豆疫苗齐全',
    citations: [],
    steps: [],
    usage: { prompt_tokens: 1, completion_tokens: 2 },
    latency_ms: 10,
  },
}

function session(id: string, title: string): AgentSessionItem {
  return { id, channel: 'app', title, message_count: 2, create_time: '2026-11-20T10:00:00' }
}

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  return mount(ChatView, {
    attachTo: document.body,
    global: { plugins: [pinia, i18n] },
  })
}

function historyTriggerOf(wrapper: ReturnType<typeof mountView>) {
  const button = wrapper.findAll('button').find(item => item.attributes('aria-label') === '历史会话')
  if (!button) throw new Error('没有找到历史会话按钮')
  return button
}

async function sendMessage(wrapper: ReturnType<typeof mountView>, text = '你好') {
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

describe('ChatView 无障碍基线', () => {
  it('消息区是带名称的 region，流式期间 aria-busy 为 true，done 后回到 false', async () => {
    const stream = controlStream()
    const wrapper = mountView()
    await flushPromises()

    const main = wrapper.get('main')
    expect(main.attributes('role')).toBe('region')
    expect(main.attributes('aria-label')).toBe('对话消息')
    expect(main.attributes('aria-busy')).toBe('false')

    await sendMessage(wrapper)
    expect(wrapper.get('main').attributes('aria-busy')).toBe('true')

    stream.handlers?.onEvent(doneEvent)
    // done 事件先到，send() 的 finally 要等流收尾后才把 streaming 置回 false
    expect(wrapper.get('main').attributes('aria-busy')).toBe('true')
    stream.finish()
    await flushPromises()

    expect(wrapper.get('main').attributes('aria-busy')).toBe('false')
    expect(wrapper.text()).toContain('豆豆疫苗齐全')

    wrapper.unmount()
  })

  it('状态播报区先说「正在回复」，done 后说「回复已完成」', async () => {
    const stream = controlStream()
    const wrapper = mountView()
    await flushPromises()

    await sendMessage(wrapper)
    expect(wrapper.get('[data-testid="chat-live"]').text()).toBe('Lumina 正在回复…')

    stream.handlers?.onEvent(doneEvent)
    await flushPromises()
    expect(wrapper.get('[data-testid="chat-live"]').text()).toBe('回复已完成')

    stream.finish()
    await flushPromises()
    wrapper.unmount()
  })

  it('错误条是 role=alert，且没有内容的空气泡被移除（既有行为不回归）', async () => {
    const stream = controlStream()
    const wrapper = mountView()
    await flushPromises()

    await sendMessage(wrapper)
    stream.handlers?.onEvent({
      event: 'error',
      data: { code: 'model_error', message: '模型超时', retryable: true },
    })
    await flushPromises()

    expect(wrapper.get('[data-testid="chat-error"]').attributes('role')).toBe('alert')
    // S1.36：已知 code 走三语文案，不再直接展示服务端中文 message
    expect(wrapper.text()).toContain('模型服务暂时不可用')
    expect(wrapper.text()).not.toContain('模型超时')
    expect(wrapper.findAll('[data-testid="chat-assistant"]')).toHaveLength(0)

    stream.finish()
    await flushPromises()
    wrapper.unmount()
  })

  it('输入框有可读名称，并由免责说明描述；页面有唯一 h1', async () => {
    const wrapper = mountView()
    await flushPromises()

    const textarea = wrapper.get('[data-testid="chat-input"]')
    expect(textarea.attributes('aria-label')).toBe('消息输入框')
    const describedBy = textarea.attributes('aria-describedby')
    expect(describedBy).toBe('chat-disclaimer')
    expect(document.getElementById(describedBy ?? '')?.textContent).toContain('兽医')

    const headings = wrapper.findAll('h1')
    expect(headings).toHaveLength(1)
    expect(headings[0].text()).toBe('Lumina')

    wrapper.unmount()
  })

  it('打开历史面板后焦点进入对话框，Esc 关闭并把焦点还给触发按钮', async () => {
    vi.mocked(fetchSessions).mockResolvedValue({ total: 2, items: [session('s1', '会话一'), session('s2', '会话二')] })
    const wrapper = mountView()
    await flushPromises()

    const trigger = historyTriggerOf(wrapper)
    await trigger.trigger('click')
    await flushPromises()

    const dialog = wrapper.get('[role="dialog"]')
    expect(dialog.attributes('aria-modal')).toBe('true')
    expect(document.activeElement).toBe(dialog.element)

    await dialog.trigger('keydown', { key: 'Escape' })
    await flushPromises()

    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
    expect(document.activeElement).toBe(trigger.element)

    wrapper.unmount()
  })

  it('Tab 在历史面板内循环：最后一个 Tab 回第一个，第一个 Shift+Tab 到最后', async () => {
    vi.mocked(fetchSessions).mockResolvedValue({ total: 2, items: [session('s1', '会话一'), session('s2', '会话二')] })
    const wrapper = mountView()
    await flushPromises()

    await historyTriggerOf(wrapper).trigger('click')
    await flushPromises()

    const buttons = wrapper.get('[role="dialog"]').findAll('button')
    expect(buttons.length).toBeGreaterThanOrEqual(3)
    const first = buttons[0].element as HTMLElement
    const last = buttons[buttons.length - 1].element as HTMLElement

    last.focus()
    await buttons[buttons.length - 1].trigger('keydown', { key: 'Tab' })
    expect(document.activeElement).toBe(first)

    first.focus()
    await buttons[0].trigger('keydown', { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(last)

    wrapper.unmount()
  })
})
