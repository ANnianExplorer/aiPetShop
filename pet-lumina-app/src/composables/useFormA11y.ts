import { nextTick, ref, type Ref } from 'vue'

export interface FormA11y {
  /** 当前表单级错误文案，空字符串表示无错误 */
  errorMessage: Ref<string>
  /** 稳定 id：提交失败的字段用 aria-describedby 指向它 */
  errorId: string
  /** 写入错误；先移除再挂载，保证同一条错误重复提交也会重新触发 role=alert 播报 */
  announce: (message: string) => Promise<void>
  /** 清空错误（用户补齐必填项或提交成功时） */
  clear: () => void
}

let sequence = 0

export function useFormA11y(scope: string): FormA11y {
  const errorMessage = ref('')
  const errorId = `${scope}-form-error-${++sequence}`

  const announce = async (message: string) => {
    errorMessage.value = ''
    await nextTick()
    errorMessage.value = message
    await nextTick()
  }

  const clear = () => {
    errorMessage.value = ''
  }

  return { errorMessage, errorId, announce, clear }
}
