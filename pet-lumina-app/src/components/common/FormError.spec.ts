import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import FormError from './FormError.vue'

describe('FormError 表单错误播报', () => {
  it('有错误时以 alert 呈现，并挂上可被 aria-describedby 引用的 id', () => {
    const wrapper = mount(FormError, {
      props: { id: 'login-form-error-1', message: '请填写完整信息' },
    })

    const alert = wrapper.find('[role="alert"]')
    expect(alert.exists()).toBe(true)
    expect(alert.attributes('id')).toBe('login-form-error-1')
    expect(alert.attributes('data-testid')).toBe('form-error')
    expect(alert.text()).toContain('请填写完整信息')
  })

  it('无错误时不渲染空节点', () => {
    const wrapper = mount(FormError, {
      props: { id: 'login-form-error-2', message: '' },
    })

    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="form-error"]').exists()).toBe(false)
  })
})
