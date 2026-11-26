import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createMemoryHistory, createRouter } from 'vue-router'
import zhCN from '@/locales/zh-CN.json'
import type { Topic } from '@/types'
import TrendingSlider from './TrendingSlider.vue'

const topics: Topic[] = [
  { id: 't1', title: '新手养猫指南', image: 'https://example.com/1.jpg', category: '指南', postCount: 12, followerCount: 34 },
  { id: 't2', title: '狗狗训练日记', image: 'https://example.com/2.jpg', category: '日常', postCount: 8, followerCount: 21 },
  { id: 't3', title: '异宠饲养交流', image: 'https://example.com/3.jpg', category: '交流', postCount: 5, followerCount: 9 },
]

const Empty = { template: '<div />' }

async function createTestRouter() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: Empty },
      { path: '/topic/:id', name: 'topicDetail', component: Empty },
      { path: '/topics', name: 'topicsList', component: Empty },
    ],
  })
  await router.push('/')
  await router.isReady()
  return router
}

function mockMatchMedia(matches: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

async function mountSlider() {
  const router = await createTestRouter()
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  return mount(TrendingSlider, {
    props: { topics },
    attachTo: document.body,
    global: { plugins: [router, i18n] },
  })
}

describe('TrendingSlider 无障碍', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    Object.defineProperty(Element.prototype, 'scrollTo', {
      configurable: true,
      writable: true,
      value: vi.fn(),
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  it('区域有标题关联，话题卡片与查看全部都是可键盘访问的链接', async () => {
    mockMatchMedia(false)
    const wrapper = await mountSlider()

    const section = wrapper.find('section')
    const heading = wrapper.find('h2')
    expect(section.attributes('aria-labelledby')).toBe(heading.attributes('id'))
    expect(heading.text()).toBe('热门话题')

    const card = wrapper.find('a[href="/topic/t1"]')
    expect(card.exists()).toBe(true)
    expect(card.attributes('aria-label')).toContain('新手养猫指南')
    expect(card.find('img').attributes('alt')).toBe('')

    const viewAll = wrapper.find('a[href="/topics"]')
    expect(viewAll.exists()).toBe(true)
    expect(viewAll.text()).toBe('查看全部')

    expect(wrapper.find('button[aria-label="上一个话题"]').attributes('disabled')).toBe('')
    expect(wrapper.find('button[aria-label="下一个话题"]').attributes('disabled')).toBeUndefined()

    wrapper.unmount()
  })

  it('prefers-reduced-motion 时不启动自动轮播', async () => {
    mockMatchMedia(true)
    vi.useFakeTimers()
    const wrapper = await mountSlider()

    await vi.advanceTimersByTimeAsync(9000)

    expect(wrapper.find('button[aria-label="上一个话题"]').attributes('disabled')).toBe('')
    expect(wrapper.find('button[aria-label="下一个话题"]').attributes('disabled')).toBeUndefined()

    wrapper.unmount()
  })

  it('普通模式下自动轮播推进，按钮禁用态跟随位置', async () => {
    mockMatchMedia(false)
    vi.useFakeTimers()
    const wrapper = await mountSlider()

    await vi.advanceTimersByTimeAsync(4000)
    expect(wrapper.find('button[aria-label="上一个话题"]').attributes('disabled')).toBeUndefined()

    await vi.advanceTimersByTimeAsync(4000)
    expect(wrapper.find('button[aria-label="下一个话题"]').attributes('disabled')).toBe('')

    wrapper.unmount()
  })
})
