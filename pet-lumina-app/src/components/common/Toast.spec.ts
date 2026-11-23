import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN.json'
import { useToast } from '@/composables/useToast'
import Toast from './Toast.vue'

const { toasts, showToast, removeToast } = useToast()

function mountToast() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  return mount(Toast, {
    attachTo: document.body,
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  toasts.value.splice(0)
  document.body.innerHTML = ''
})

afterEach(() => {
  vi.useRealTimers()
  document.body.innerHTML = ''
})

describe('Toast 状态播报', () => {
  it('容器是 polite live region，成功提示没有 alert 语义', async () => {
    showToast('已保存', 'success')
    const wrapper = mountToast()
    await flushPromises()

    const region = document.querySelector('[role="status"]')
    expect(region).not.toBeNull()
    expect(region?.getAttribute('aria-live')).toBe('polite')
    expect(region?.getAttribute('aria-atomic')).toBe('true')
    expect(region?.textContent).toContain('已保存')
    expect(document.querySelector('[role="alert"]')).toBeNull()

    wrapper.unmount()
  })

  it('错误提示升级为 role=alert', async () => {
    showToast('保存失败', 'error')
    const wrapper = mountToast()
    await flushPromises()

    const alert = document.querySelector('[role="alert"]')
    expect(alert).not.toBeNull()
    expect(alert?.textContent).toContain('保存失败')

    wrapper.unmount()
  })

  it('关闭按钮有可读名称，点击后从队列移除', async () => {
    showToast('可关闭', 'info')
    const wrapper = mountToast()
    await flushPromises()

    const close = document.querySelector<HTMLButtonElement>('button[aria-label="关闭"]')
    expect(close).not.toBeNull()
    close?.click()
    await flushPromises()

    expect(toasts.value).toHaveLength(0)

    wrapper.unmount()
  })

  it('到时自动移除，不留在队列里', () => {
    vi.useFakeTimers()
    showToast('稍纵即逝', 'success', 1000)
    expect(toasts.value).toHaveLength(1)

    vi.advanceTimersByTime(1001)

    expect(toasts.value).toHaveLength(0)
  })

  it('removeToast 是幂等的：重复移除同一条不会误删别的提示', () => {
    showToast('第一条', 'success', 9999)
    showToast('第二条', 'success', 9999)
    const firstId = toasts.value[0].id

    removeToast(firstId)
    removeToast(firstId)

    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('第二条')
  })
})
