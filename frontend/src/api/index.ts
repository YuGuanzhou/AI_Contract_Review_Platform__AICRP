import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, refreshToken } from '@/utils/auth'
import router from '@/router'

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 添加 token 到请求头
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 如果是文件上传，修改 Content-Type
    if (config.data instanceof FormData) {
      config.headers['Content-Type'] = 'multipart/form-data'
    }
    
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    
    // 处理业务错误
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    
    return data
  },
  async (error) => {
    const { response, config } = error

    // 处理 HTTP 错误
    if (response) {
      const { status, data } = response

      // 登录/刷新接口的 401 是「凭据错误」，不是 token 过期，
      // 直接交给调用方（Login.vue）提示，避免双重提示「登录已过期」+「用户名或密码错误」
      const isAuthEndpoint =
        typeof config?.url === 'string' &&
        (config.url.includes('/auth/login') || config.url.includes('/auth/refresh'))

      switch (status) {
        case 401:
          if (isAuthEndpoint) {
            return Promise.reject(error)
          }
          // token 过期，尝试刷新
          if (!config._retry) {
            config._retry = true
            const refreshed = await refreshToken()
            if (refreshed) {
              return service(config)
            }
          }
          // 刷新失败（或重试后仍 401），跳转登录页
          ElMessage.error('登录已过期，请重新登录')
          router.push('/login')
          break
          
        case 403:
          ElMessage.error('权限不足')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 500:
          ElMessage.error('服务器内部错误')
          break
          
        default:
          ElMessage.error(data?.message || '请求失败')
      }
    } else {
      // 网络错误
      ElMessage.error('网络连接失败，请检查网络设置')
    }
    
    return Promise.reject(error)
  }
)

// 导出常用的请求方法
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.patch(url, data, config)
  },
  
  upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}

export default service