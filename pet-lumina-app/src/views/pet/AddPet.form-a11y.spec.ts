import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createPinia, setActivePinia } from 'pinia'
import zhCN from '@/locales/zh-CN.json'
import AddPet from './AddPet.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}))

vi.mock('@/api/file', () => ({
  fileApi: {
    uploadImage: vi.fn().mockResolvedValue('https://example.com/avatar.png'),
  },
}))

function mountAddPet() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(AddPet, {
    attachTo: document.body,
    global: { plugins: [i18n, pinia] },
  })
}

describe('AddPet 表单错误播报', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('空表单提交时播报 alert、标记名字/类型/品种并聚焦名字', async () => {
    const wrapper = mountAddPet()

    await wrapper.find('main > button').trigger('click')
    await flushPromises()

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.text()).toContain('请填写宠物名字、类型和品种')

    const name = wrapper.find('#add-pet-name')
    const breed = wrapper.find('#add-pet-breed')
    const typeGroup = wrapper.find('[role="group"][aria-labelledby="add-pet-type-label"]')

    expect(name.attributes('aria-invalid')).toBe('true')
    expect(breed.attributes('aria-invalid')).toBe('true')
    expect(typeGroup.attributes('aria-invalid')).toBe('true')
    expect(name.attributes('aria-describedby')).toBe(alert.attributes('id'))
    expect(document.activeElement).toBe(name.element)

    wrapper.unmount()
  })

  it('宠物类型按钮用 aria-pressed 表达选中状态', async () => {
    const wrapper = mountAddPet()

    const typeButtons = wrapper.findAll('button[aria-pressed]')
    expect(typeButtons).toHaveLength(3)
    expect(typeButtons.every(button => button.attributes('aria-pressed') === 'false')).toBe(true)

    await typeButtons[1].trigger('click')

    expect(typeButtons[1].attributes('aria-pressed')).toBe('true')
    expect(typeButtons[0].attributes('aria-pressed')).toBe('false')
    expect(typeButtons[2].attributes('aria-pressed')).toBe('false')

    wrapper.unmount()
  })

  it('头像上传是带名称的按钮，上传后预览图都是装饰图', async () => {
    const wrapper = mountAddPet()

    const upload = wrapper.find('button[aria-label="上传宠物头像"]')
    expect(upload.exists()).toBe(true)
    expect(upload.attributes('type')).toBe('button')

    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      writable: true,
      value: vi.fn(() => 'blob:avatar'),
    })
    const fileInput = wrapper.find('input[type="file"]')
    const file = new File(['avatar'], 'avatar.png', { type: 'image/png' })
    Object.defineProperty(fileInput.element, 'files', {
      configurable: true,
      value: [file],
    })

    await fileInput.trigger('change')
    await flushPromises()

    const images = wrapper.findAll('img')
    expect(images).toHaveLength(2)
    expect(images.every(image => image.attributes('alt') === '')).toBe(true)

    wrapper.unmount()
  })
})
