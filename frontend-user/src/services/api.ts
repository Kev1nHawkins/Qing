import axios from 'axios'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  requestId: string
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || '网络异常，请稍后重试'
    return Promise.reject(new Error(message))
  },
)

