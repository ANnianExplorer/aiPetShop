import { describe, expect, it } from 'vitest'
import { watch } from 'vue'
import { useFormA11y } from './useFormA11y'

describe('useFormA11y', () => {
  it('重复播报同一条错误时先清空再写入，保证 live region 重新触发', async () => {
    const { errorMessage, announce } = useFormA11y('login')

    await announce('请填写完整信息')
    expect(errorMessage.value).toBe('请填写完整信息')

    const seen: string[] = []
    watch(errorMessage, (value) => seen.push(value), { flush: 'sync' })

    await announce('请填写完整信息')
    expect(seen).toEqual(['', '请填写完整信息'])
    expect(errorMessage.value).toBe('请填写完整信息')
  })

  it('不同表单实例的 errorId 不重复', () => {
    const first = useFormA11y('login')
    const second = useFormA11y('login')

    expect(first.errorId).toMatch(/^login-form-error-\d+$/)
    expect(second.errorId).toMatch(/^login-form-error-\d+$/)
    expect(first.errorId).not.toBe(second.errorId)
  })

  it('clear 清空当前错误', async () => {
    const { errorMessage, announce, clear } = useFormA11y('clear-test')

    await announce('出错了')
    expect(errorMessage.value).toBe('出错了')

    clear()
    expect(errorMessage.value).toBe('')
  })
})
