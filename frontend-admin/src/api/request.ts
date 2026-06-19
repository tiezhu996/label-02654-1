import axios, { AxiosError } from 'axios'
import { message } from 'antd'

// Custom params serializer to properly encode Chinese characters
const paramsSerializer = (params: Record<string, unknown>): string => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })
  return searchParams.toString()
}

// Create axios instance
const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer,
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error: AxiosError<{ detail?: string }>) => {
    const errorMessage = error.response?.data?.detail || '请求失败，请稍后重试'
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
      message.error('登录已过期，请重新登录')
    } else if (error.response?.status === 403) {
      message.error('没有权限执行此操作')
    } else {
      message.error(errorMessage)
    }
    
    return Promise.reject(error)
  }
)

export default request
