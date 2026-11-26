import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import zhCN from '@/locales/zh-CN.json'
import AddReminder from './AddReminder.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

function mountAddReminder() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(AddReminder, {
    attachTo: document.body,
    global: { plugins: [i18n, pinia] },
  })
}

function findButton(wrapper: VueWrapper, text: string) {
  const button = wrapper.findAll('button').find((item) => item.text().includes(text))
  if (!button) throw new Error(`未找到按钮：${text}`)
  return button
}

describe('AddReminder 表单错误播报', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('空标题保存时播报 alert、标记输入框并把焦点移到标题', async () => {
    const wrapper = mountAddReminder()

    await findButton(wrapper, '保存').trigger('click')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('请输入提醒标题')

    const title = wrapper.find('#reminder-title')
    expect(title.attributes('aria-invalid')).toBe('true')
    expect(title.attributes('aria-describedby')).toBe(alert.attributes('id'))
    expect(document.activeElement).toBe(title.element)

    wrapper.unmount()
  })

  it('填写标题后错误与 aria-invalid 自动清除', async () => {
    const wrapper = mountAddReminder()

    await findButton(wrapper, '保存').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)

    await wrapper.find('#reminder-title').setValue('给猫咪喂药')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('#reminder-title').attributes('aria-invalid')).toBeUndefined()

    wrapper.unmount()
  })

  it('类型与重复选项通过 aria-pressed 暴露选中状态', async () => {
    const wrapper = mountAddReminder()

    const pressed = wrapper.findAll('button[aria-pressed]')
    expect(pressed).toHaveLength(7)
    expect(wrapper.findAll('button[aria-pressed="true"]')).toHaveLength(2)

    const medical = findButton(wrapper, '医疗健康')
    await medical.trigger('click')
    expect(medical.attributes('aria-pressed')).toBe('true')
    expect(findButton(wrapper, '日常护理').attributes('aria-pressed')).toBe('false')

    const dailyRepeat = wrapper
      .findAll('button[aria-pressed]')
      .find((item) => item.text().trim() === '每天')
    if (!dailyRepeat) throw new Error('未找到「每天」重复选项')
    await dailyRepeat.trigger('click')
    expect(dailyRepeat.attributes('aria-pressed')).toBe('true')

    wrapper.unmount()
  })
})
