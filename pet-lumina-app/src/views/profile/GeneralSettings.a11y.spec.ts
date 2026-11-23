import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN.json'
import { useDarkMode } from '@/composables/useDarkMode'
import GeneralSettings from './GeneralSettings.vue'

const back = vi.fn()
const i18nMocks = vi.hoisted(() => ({ setLocale: vi.fn() }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ back }),
}))

vi.mock('@/i18n', () => ({
  setLocale: i18nMocks.setLocale,
}))

const { isDark } = useDarkMode()

function mountSettings() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  return mount(GeneralSettings, {
    attachTo: document.body,
    global: { plugins: [i18n] },
  })
}

function dialogEl(): HTMLElement | null {
  return document.querySelector<HTMLElement>('[role="dialog"]')
}

beforeEach(() => {
  localStorage.clear()
  isDark.value = false
  back.mockClear()
  i18nMocks.setLocale.mockClear()
  document.body.innerHTML = ''
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('GeneralSettings 无障碍', () => {
  it('页面有唯一 h1，返回按钮有可读名称并触发返回', async () => {
    const wrapper = mountSettings()

    const headings = wrapper.findAll('h1')
    expect(headings).toHaveLength(1)
    expect(headings[0].text()).toBe('通用设置')

    const backButton = wrapper.get('button[aria-label="返回"]')
    await backButton.trigger('click')
    expect(back).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })

  it('热点推送与深色模式都是 switch，并带 aria-checked', async () => {
    const wrapper = mountSettings()

    const switches = wrapper.findAll('[role="switch"]')
    expect(switches).toHaveLength(2)

    const hotPush = switches.find(item => item.attributes('aria-label') === '热点推送')
    const darkMode = switches.find(item => item.attributes('aria-label') === '深色模式')
    expect(hotPush).toBeDefined()
    expect(darkMode).toBeDefined()

    expect(hotPush?.attributes('aria-checked')).toBe('false')
    expect(hotPush?.attributes('aria-disabled')).toBe('true')
    expect(darkMode?.attributes('aria-checked')).toBe('false')

    wrapper.unmount()
  })

  it('点击深色模式开关后 aria-checked 真实翻转', async () => {
    const wrapper = mountSettings()

    const darkMode = wrapper.findAll('[role="switch"]')
      .find(item => item.attributes('aria-label') === '深色模式')
    expect(darkMode).toBeDefined()

    await darkMode?.trigger('click')

    expect(darkMode?.attributes('aria-checked')).toBe('true')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    wrapper.unmount()
  })

  it('语言弹窗是 aria-modal 对话框，打开后焦点进入、Esc 关闭并把焦点还给触发按钮', async () => {
    const wrapper = mountSettings()
    const trigger = wrapper.get('button[aria-haspopup="dialog"]')

    await trigger.trigger('click')
    await flushPromises()

    const dialog = dialogEl()
    expect(dialog).not.toBeNull()
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    const labelledBy = dialog?.getAttribute('aria-labelledby') ?? ''
    expect(document.getElementById(labelledBy)?.textContent).toBe('选择语言')
    expect(document.activeElement).toBe(dialog)

    dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await flushPromises()

    expect(dialogEl()).toBeNull()
    expect(document.activeElement).toBe(trigger.element)

    wrapper.unmount()
  })

  it('Tab 在弹窗内首尾循环', async () => {
    const wrapper = mountSettings()
    await wrapper.get('button[aria-haspopup="dialog"]').trigger('click')
    await flushPromises()

    const dialog = dialogEl()
    const buttons = dialog?.querySelectorAll<HTMLButtonElement>('button') ?? []
    expect(buttons.length).toBeGreaterThanOrEqual(4)
    const first = buttons[0]
    const last = buttons[buttons.length - 1]

    last.focus()
    last.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }))
    expect(document.activeElement).toBe(first)

    first.focus()
    first.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true }))
    expect(document.activeElement).toBe(last)

    wrapper.unmount()
  })

  it('选择语言会调用 setLocale 并关闭弹窗', async () => {
    const wrapper = mountSettings()
    await wrapper.get('button[aria-haspopup="dialog"]').trigger('click')
    await flushPromises()

    const dialog = dialogEl()
    const languageButtons = Array.from(dialog?.querySelectorAll<HTMLButtonElement>('button') ?? [])
    // [关闭, 简体中文, English, 日本語]
    languageButtons[2].click()
    await flushPromises()

    expect(i18nMocks.setLocale).toHaveBeenCalledWith('en-US')
    expect(dialogEl()).toBeNull()

    wrapper.unmount()
  })
})
