import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import zhCN from '@/locales/zh-CN.json'
import EditProfile from './EditProfile.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

function mountEditProfile() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(EditProfile, {
    attachTo: document.body,
    global: { plugins: [i18n, pinia] },
  })
}

function findButton(wrapper: VueWrapper, text: string) {
  const button = wrapper.findAll('button').find((item) => item.text().includes(text))
  if (!button) throw new Error(`未找到按钮：${text}`)
  return button
}

describe('EditProfile 表单错误播报', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('用户名为空时播报 alert、标记输入框并把焦点移到用户名', async () => {
    const wrapper = mountEditProfile()

    await wrapper.find('#profile-nickname').setValue('')
    await findButton(wrapper, '保存').trigger('click')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('请输入用户名')

    const nickname = wrapper.find('#profile-nickname')
    expect(nickname.attributes('aria-invalid')).toBe('true')
    expect(nickname.attributes('aria-describedby')).toBe(alert.attributes('id'))
    expect(document.activeElement).toBe(nickname.element)

    wrapper.unmount()
  })

  it('填写用户名后错误与 aria-invalid 自动清除', async () => {
    const wrapper = mountEditProfile()

    await wrapper.find('#profile-nickname').setValue('')
    await findButton(wrapper, '保存').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)

    await wrapper.find('#profile-nickname').setValue('小鱼')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('#profile-nickname').attributes('aria-invalid')).toBeUndefined()

    wrapper.unmount()
  })
})
