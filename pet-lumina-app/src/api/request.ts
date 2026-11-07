import axios, { type AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { showToast, type ToastOptions } from 'vant'
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

/** 后端统一响应封装 BaseResponse */
interface ApiEnvelope {
  code?: number
  data?: unknown
  message?: string
}

/** 后端错误响应体（HTTP 4xx/5xx 时由 axios 抛到错误分支） */
interface ApiErrorPayload {
  code?: number
  message?: string
}

/** axios 的 response.request 类型为 any，这里只声明实际用到的原始文本字段 */
interface RawResponse {
  responseText?: string
}

/**
 * 处理 JSON 中超大数字的精度丢失问题
 * 将超过安全整数范围的数字转为字符串
 */
function parseJsonWithBigInt(jsonStr: string): unknown {
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

/** 把未知的解析结果收窄为响应封装，非对象一律视为空封装（code 为 undefined） */
function toEnvelope(value: unknown): ApiEnvelope {
  return typeof value === 'object' && value !== null ? (value as ApiEnvelope) : {}
}

/** 优先用原始文本重新解析，避免 axios 已丢失大整数精度 */
function parseResponseBody(response: AxiosResponse): unknown {
  if (typeof response.data === 'string') {
    try {
      return parseJsonWithBigInt(response.data)
    } catch {
      return response.data
    }
  }
  // axios 已经 JSON.parse 过了，大数字可能已丢失精度
  // 用原始文本重新解析
  const rawText = (response.request as RawResponse | undefined)?.responseText
  if (typeof rawText === 'string' && rawText) {
    try {
      return parseJsonWithBigInt(rawText)
    } catch {
      return response.data
    }
  }
  return response.data
}

/** 频率限制提示（Vant 4 的 ToastType 没有 warning，沿用普通文本样式） */
function showRateLimitToast(message?: string) {
  const options: ToastOptions = {
    message: message || '操作过于频繁，请稍后再试',
  }
  showToast(options)
}

/**
 * 分页结构归一化：MyBatis Plus 的 total/current 是 long，
 * 经 JsonConfig 的 ToStringSerializer 会变成字符串，这里转回 number 以匹配 PageResult<T>。
 */
function normalizePageResult(value: unknown): unknown {
  if (typeof value !== 'object' || value === null) return value
  const page = value as { records?: unknown; total?: unknown; current?: unknown }
  if (!Array.isArray(page.records)) return value
  const normalized: { records?: unknown; total?: unknown; current?: unknown } = { ...page }
  for (const key of ['total', 'current'] as const) {
    const raw = normalized[key]
    if (typeof raw === 'string' && raw !== '' && Number.isFinite(Number(raw))) {
      normalized[key] = Number(raw)
    }
  }
  return normalized
}

/**
 * axios 的响应拦截器签名要求回调返回 AxiosResponse，
 * 但这里刻意返回解包后的 data —— 收窄管理器签名以表达真实行为。
 */
interface DataUnwrappingInterceptor {
  use(
    onFulfilled: (response: AxiosResponse) => unknown,
    onRejected?: (error: AxiosError<ApiErrorPayload>) => unknown
  ): number
}

const responseInterceptor = request.interceptors.response as unknown as DataUnwrappingInterceptor

// 响应拦截器：统一处理返回数据
responseInterceptor.use(
  (response: AxiosResponse) => {
    const envelope = toEnvelope(parseResponseBody(response))

    if (envelope.code !== 0) {
      if (envelope.code === 42900) {
        showRateLimitToast(envelope.message)
      } else {
        showToast(envelope.message || '请求失败')
      }
      if (envelope.code === 40100) {
        localStorage.removeItem('satoken')
        window.location.hash = '#/login'
      }
      return Promise.reject(new Error(envelope.message || '请求失败'))
    }
    return normalizePageResult(envelope.data)
  },
  (error: AxiosError<ApiErrorPayload>) => {
    // 后端现在按业务语义返回真实 HTTP 状态（400/401/403/404/429/500），
    // axios 会走这里；仍要按业务码提示，否则用户只看到“网络错误”。
    const data = error.response?.data
    if (data && typeof data.code === 'number') {
      if (data.code === 42900) {
        showRateLimitToast(data.message)
      } else {
        showToast(data.message || '请求失败')
      }
      if (data.code === 40100) {
        localStorage.removeItem('satoken')
        window.location.hash = '#/login'
      }
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    showToast('网络错误，请稍后重试')
    return Promise.reject(error)
  }
)

/**
 * 类型安全的请求门面：响应拦截器已经把 BaseResponse 解包成 data，
 * 所以这里的泛型 T 就是业务数据类型（而非 AxiosResponse<T>）。
 */
export interface ApiClient {
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
}

const apiClient = request as unknown as ApiClient

export default apiClient
