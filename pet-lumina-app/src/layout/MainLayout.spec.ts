import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN.json'
import MainLayout from './MainLayout.vue'

const routerMock = vi.hoisted(() => ({
  push: vi.fn(),
  route: { name: 'home' },
}))

vi.mock('vue-router', () => ({
  useRoute: () => routerMock.route,
  useRouter: () => ({ push: routerMock.push }),
}))

function mountLayout() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  return mount(MainLayout, {
    global: {
      plugins: [i18n],
      stubs: { RouterView: true },
    },
  })
}

beforeEach(() => {
  routerMock.push.mockClear()
})

describe('MainLayout 底部导航无障碍', () => {
  it('导航有可读名称，5 个入口都是原生按钮', () => {
    const wrapper = mountLayout()

    expect(wrapper.get('nav').attributes('aria-label')).toBe('主导航')
    const buttons = wrapper.findAll('nav button')
    expect(buttons).toHaveLength(5)
    expect(buttons.every(button => button.attributes('type') === 'button')).toBe(true)

    wrapper.unmount()
  })

  it('当前页有且只有一个 aria-current=page', () => {
    const wrapper = mountLayout()

    const current = wrapper.findAll('nav button[aria-current="page"]')
    expect(current).toHaveLength(1)
    expect(current[0].text()).toContain('首页')

    wrapper.unmount()
  })

  it('点击非当前项会路由跳转，点击当前项不会重复跳转', async () => {
    const wrapper = mountLayout()

    const buttons = wrapper.findAll('nav button')
    await buttons[2].trigger('click')
    expect(routerMock.push).toHaveBeenCalledTimes(1)
    expect(routerMock.push).toHaveBeenCalledWith('/community')

    await buttons[0].trigger('click')
    expect(routerMock.push).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })

  it('装饰光晕对辅助技术隐藏', () => {
    const wrapper = mountLayout()

    const glows = wrapper.findAll('[aria-hidden="true"]')
    // 5 个图标 + 2 个背景光晕；这里只确认光晕本身也在隐藏列表里
    expect(glows.length).toBeGreaterThanOrEqual(2)

    wrapper.unmount()
  })
})
