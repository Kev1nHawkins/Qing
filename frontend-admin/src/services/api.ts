import axios from 'axios'
import {
  ADMIN_TOKEN_KEY,
  redirectToAdminLogin,
} from '@/services/adminSession'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ADMIN_TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || '请求失败'
    const requestUrl = String(error.config?.url || '')
    if (!requestUrl.includes('/auth/login')) {
      if (error.response?.status === 401) {
        redirectToAdminLogin('登录状态已过期，请重新登录。')
      } else if (error.response?.status === 403) {
        redirectToAdminLogin('当前账号没有管理员权限。')
      }
    }
    return Promise.reject(new Error(message))
  },
)

