import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createMemoryHistory, createRouter } from 'vue-router'
import zhCN from '@/locales/zh-CN.json'
import LogCard from './LogCard.vue'
import type { LogEntry } from '@/types'

function makeLog(overrides: Partial<LogEntry> = {}): LogEntry {
  return {
    id: 'l1',
    userId: 'u1',
    petId: 'pet1',
    type: 'walking',
    title: '晨间散步',
    content: '沿着河边走了两公里',
    imageList: ['https://example.com/log.jpg'],
    tagList: ['户外'],
    likes: 5,
    createTime: '2026-11-24 08:00',
    ...overrides,
  }
}

async function mountCard(log: LogEntry) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/logs', name: 'lifeLog', component: { template: '<div />' } },
      { path: '/log/:id', name: 'logDetail', component: { template: '<div />' } },
    ],
  })
  await router.push('/logs')
  await router.isReady()

  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const wrapper = mount(LogCard, {
    props: { log },
    attachTo: document.body,
    global: { plugins: [router, i18n] },
  })
  return { wrapper, router }
}

beforeEach(() => {
  document.body.innerHTML = ''
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('LogCard 无障碍', () => {
  it('整卡是链接，名称包含记录标题', async () => {
    const { wrapper } = await mountCard(makeLog())

    const link = wrapper.get('a[href="/log/l1"]')
    expect(link.attributes('aria-label')).toBe('查看生活记录：晨间散步')
    expect(link.classes()).toContain('break-inside-avoid')

    wrapper.unmount()
  })

  it('记录图有描述，类型图标对读屏隐藏', async () => {
    const { wrapper } = await mountCard(makeLog())

    expect(wrapper.get('img[alt="记录图片：晨间散步"]').attributes('src')).toBe(
      'https://example.com/log.jpg',
    )
    expect(wrapper.find('[aria-hidden="true"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('没有图片时仍保留链接与标题', async () => {
    const { wrapper } = await mountCard(makeLog({ imageList: [] }))

    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.get('a[aria-label="查看生活记录：晨间散步"]').text()).toContain('晨间散步')

    wrapper.unmount()
  })
})
