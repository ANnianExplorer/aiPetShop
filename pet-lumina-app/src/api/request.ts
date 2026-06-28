import axios from 'axios'
import { showToast } from 'vant'
import 'vant/es/toast/style'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
})

// 请求拦截器：注入 token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('satoken')
    if (token) {
      config.headers['satoken'] = token
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * 处理 JSON 中超大数字的精度丢失问题
 * 将超过安全整数范围的数字转为字符串
 */
function parseJsonWithBigInt(jsonStr: string): any {
  // 匹配 JSON 中的数字值（包括负数和小数），但排除已经是字符串的
  const safeStr = jsonStr.replace(/"(?:[^"\\]|\\.)*"|(-?\d{16,}(?:\.\d+)?(?:[eE][+-]?\d+)?)/g, (match, num) => {
    if (num) {
      // 超过16位的整数转为字符串
      return `"${num}"`
    }
    return match // 字符串部分保持不变
  })
  return JSON.parse(safeStr)
}

// 响应拦截器：统一处理返回数据
request.interceptors.response.use(
  (response) => {
    // 处理大数字精度问题
    let res: any
    if (typeof response.data === 'string') {
      try {
        res = parseJsonWithBigInt(response.data)
      } catch {
        res = response.data
      }
    } else {
      // axios 已经 JSON.parse 过了，大数字可能已丢失精度
      // 用原始文本重新解析
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
    }

    if (res.code !== 0) {
      if (res.code === 42900) {
        showToast({ message: res.message || '操作过于频繁，请稍后再试', type: 'warning' } as any)
      } else {
        showToast(res.message || '请求失败')
      }
      if (res.code === 40100) {
        localStorage.removeItem('satoken')
        window.location.hash = '#/login'
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res.data as any
  },
  (error) => {
    showToast('网络错误，请稍后重试')
    return Promise.reject(error)
  }
)

export default request
