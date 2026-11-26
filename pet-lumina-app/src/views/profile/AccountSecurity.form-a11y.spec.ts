import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import zhCN from '@/locales/zh-CN.json'
import AccountSecurity from './AccountSecurity.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

function mountAccountSecurity() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(AccountSecurity, {
    attachTo: document.body,
    global: { plugins: [i18n, pinia] },
  })
}

function findButton(wrapper: VueWrapper, text: string) {
  const button = wrapper.findAll('button').find((item) => item.text() === text)
  if (!button) throw new Error(`未找到按钮：${text}`)
  return button
}

describe('AccountSecurity 表单错误播报', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('空密码提交时播报 alert、标记三个字段并把焦点移到旧密码', async () => {
    const wrapper = mountAccountSecurity()

    await findButton(wrapper, '修改密码').trigger('click')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('请填写所有密码字段')

    for (const id of [
      'security-old-password',
      'security-new-password',
      'security-confirm-password',
    ]) {
      const input = wrapper.find(`#${id}`)
      expect(input.attributes('aria-invalid')).toBe('true')
      expect(input.attributes('aria-describedby')).toBe(alert.attributes('id'))
    }
    expect(document.activeElement).toBe(wrapper.find('#security-old-password').element)

    wrapper.unmount()
  })

  it('两次新密码不一致时播报 alert 并聚焦确认框', async () => {
    const wrapper = mountAccountSecurity()

    await wrapper.find('#security-old-password').setValue('oldpass')
    await wrapper.find('#security-new-password').setValue('newpass1')
    await wrapper.find('#security-confirm-password').setValue('newpass2')
    await findButton(wrapper, '修改密码').trigger('click')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('两次密码输入不一致')
    expect(wrapper.find('#security-old-password').attributes('aria-invalid')).toBeUndefined()
    expect(wrapper.find('#security-new-password').attributes('aria-invalid')).toBeUndefined()
    expect(wrapper.find('#security-confirm-password').attributes('aria-invalid')).toBe('true')
    expect(document.activeElement).toBe(
      wrapper.find('#security-confirm-password').element,
    )

    wrapper.unmount()
  })

  it('确认密码改成一致后错误与 aria-invalid 自动清除', async () => {
    const wrapper = mountAccountSecurity()

    await wrapper.find('#security-old-password').setValue('oldpass')
    await wrapper.find('#security-new-password').setValue('newpass1')
    await wrapper.find('#security-confirm-password').setValue('newpass2')
    await findButton(wrapper, '修改密码').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)

    await wrapper.find('#security-confirm-password').setValue('newpass1')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(
      wrapper.find('#security-confirm-password').attributes('aria-invalid'),
    ).toBeUndefined()

    wrapper.unmount()
  })
})
