import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import zhCN from '@/locales/zh-CN.json'
import Login from './Login.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

function mountLogin() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(Login, {
    attachTo: document.body,
    global: { plugins: [i18n, pinia] },
  })
}

describe('Login 表单错误播报', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('空表单提交时播报 alert、标记两个字段并把焦点移到手机号', async () => {
    const wrapper = mountLogin()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('请填写完整信息')

    const phone = wrapper.find('[data-testid="login-phone"]')
    const password = wrapper.find('[data-testid="login-password"]')
    expect(phone.attributes('aria-invalid')).toBe('true')
    expect(password.attributes('aria-invalid')).toBe('true')
    expect(phone.attributes('aria-describedby')).toBe(alert.attributes('id'))
    expect(password.attributes('aria-describedby')).toBe(alert.attributes('id'))
    expect(document.activeElement).toBe(phone.element)

    wrapper.unmount()
  })

  it('只缺密码时把焦点移到密码框', async () => {
    const wrapper = mountLogin()

    await wrapper.find('[data-testid="login-phone"]').setValue('13800000000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('[data-testid="login-phone"]').attributes('aria-invalid')).toBeUndefined()
    expect(wrapper.find('[data-testid="login-password"]').attributes('aria-invalid')).toBe('true')
    expect(document.activeElement).toBe(wrapper.find('[data-testid="login-password"]').element)

    wrapper.unmount()
  })

  it('补齐字段后错误与 aria-invalid 自动清除', async () => {
    const wrapper = mountLogin()

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)

    await wrapper.find('[data-testid="login-phone"]').setValue('13800000000')
    await wrapper.find('[data-testid="login-password"]').setValue('secret')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="login-phone"]').attributes('aria-invalid')).toBeUndefined()
    expect(wrapper.find('[data-testid="login-password"]').attributes('aria-invalid')).toBeUndefined()

    wrapper.unmount()
  })
})
