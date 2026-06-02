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

// 响应拦截器：统一处理返回数据
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 0) {
      showToast(res.message || '请求失败')
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
