import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import zhCN from '@/locales/zh-CN.json'
import SignUp from './SignUp.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

function mountSignUp() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(SignUp, {
    attachTo: document.body,
    global: { plugins: [i18n, pinia] },
  })
}

function findButton(wrapper: VueWrapper, text: string) {
  const button = wrapper.findAll('button').find((item) => item.text().includes(text))
  if (!button) throw new Error(`未找到按钮：${text}`)
  return button
}

describe('SignUp 表单错误播报', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('空表单提交时播报 alert、标记三个字段并把焦点移到手机号', async () => {
    const wrapper = mountSignUp()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('请填写完整信息')

    for (const id of ['signup-phone', 'signup-code', 'signup-password']) {
      const input = wrapper.find(`#${id}`)
      expect(input.attributes('aria-invalid')).toBe('true')
      expect(input.attributes('aria-describedby')).toBe(alert.attributes('id'))
    }
    expect(document.activeElement).toBe(wrapper.find('#signup-phone').element)

    wrapper.unmount()
  })

  it('手机号为空时点获取验证码只标记手机号并聚焦', async () => {
    const wrapper = mountSignUp()

    await findButton(wrapper, '获取验证码').trigger('click')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('请先输入手机号')
    expect(wrapper.find('#signup-phone').attributes('aria-invalid')).toBe('true')
    expect(wrapper.find('#signup-code').attributes('aria-invalid')).toBeUndefined()
    expect(wrapper.find('#signup-password').attributes('aria-invalid')).toBeUndefined()
    expect(document.activeElement).toBe(wrapper.find('#signup-phone').element)

    wrapper.unmount()
  })

  it('补齐三个字段后错误与 aria-invalid 自动清除', async () => {
    const wrapper = mountSignUp()

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)

    await wrapper.find('#signup-phone').setValue('13800000000')
    await wrapper.find('#signup-code').setValue('123456')
    await wrapper.find('#signup-password').setValue('secret')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    for (const id of ['signup-phone', 'signup-code', 'signup-password']) {
      expect(wrapper.find(`#${id}`).attributes('aria-invalid')).toBeUndefined()
    }

    wrapper.unmount()
  })
})
