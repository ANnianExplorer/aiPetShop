import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('satoken')
  if (token) {
    config.headers['satoken'] = token
  }
  return config
})

/**
 * 处理 JSON 中超大数字的精度丢失问题
 */
function parseJsonWithBigInt(jsonStr: string): any {
  const safeStr = jsonStr.replace(/"(?:[^"\\]|\\.)*"|(-?\d{16,}(?:\.\d+)?(?:[eE][+-]?\d+)?)/g, (match, num) => {
    if (num) return `"${num}"`
    return match
  })
  return JSON.parse(safeStr)
}

request.interceptors.response.use(
  (response) => {
    let res: any
    const rawText = (response as any).request?.responseText
    if (rawText) {
      try {
        res = parseJsonWithBigInt(rawText)
      } catch {
        res = response.data
      }
    } else {
      res = response.data
    }

    if (res.code !== 0) {
      if (res.code === 42900) {
        ElMessage.warning(res.message || '操作过于频繁，请稍后再试')
      } else {
        ElMessage.error(res.message || '请求失败')
      }
      if (res.code === 40100) {
        localStorage.removeItem('satoken')
        router.push('/login')
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res.data
  },
  (error) => {
    // 后端按业务语义返回真实 HTTP 状态（400/401/403/404/429/500），axios 走这里；
    // 仍然优先展示业务码里的 message，避免统一退化成“网络错误”。
    const data = (error as any)?.response?.data
    if (data && typeof data.code === 'number') {
      if (data.code === 42900) {
        ElMessage.warning(data.message || '操作过于频繁，请稍后再试')
      } else {
        ElMessage.error(data.message || '请求失败')
      }
      if (data.code === 40100) {
        localStorage.removeItem('satoken')
        router.push('/login')
      }
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    ElMessage.error('网络错误，请稍后重试')
    return Promise.reject(error)
  }
)

export default request
