import Cookies from 'js-cookie'
import { authApi } from '@/api/auth'

// Token 相关常量
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_INFO_KEY = 'user_info'

// 获取访问令牌
export function getToken(): string | null {
  return Cookies.get(ACCESS_TOKEN_KEY) || localStorage.getItem(ACCESS_TOKEN_KEY) || null
}

// 获取刷新令牌
export function getRefreshToken(): string | null {
  return Cookies.get(REFRESH_TOKEN_KEY) || localStorage.getItem(REFRESH_TOKEN_KEY) || null
}

// 设置令牌
export function setToken(accessToken: string, refreshToken?: string): void {
  // 优先使用 Cookies，如果不可用则使用 localStorage
  try {
    Cookies.set(ACCESS_TOKEN_KEY, accessToken, { expires: 7 }) // 7天过期
    if (refreshToken) {
      Cookies.set(REFRESH_TOKEN_KEY, refreshToken, { expires: 30 }) // 30天过期
    }
  } catch (error) {
    // Cookies 不可用，使用 localStorage
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    }
  }
}

// 移除令牌
export function removeToken(): void {
  try {
    Cookies.remove(ACCESS_TOKEN_KEY)
    Cookies.remove(REFRESH_TOKEN_KEY)
  } catch (error) {
    // Cookies 不可用，使用 localStorage
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
  localStorage.removeItem(USER_INFO_KEY)
}

// 刷新令牌
export async function refreshToken(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return false
  }

  try {
    const response = await authApi.refreshToken({ refresh_token: refreshToken })
    setToken(response.access_token, response.refresh_token)
    return true
  } catch (error) {
    console.error('刷新令牌失败:', error)
    removeToken()
    return false
  }
}

// 获取用户信息
export function getUserInfo(): any | null {
  const userInfoStr = localStorage.getItem(USER_INFO_KEY)
  if (!userInfoStr) {
    return null
  }

  try {
    return JSON.parse(userInfoStr)
  } catch (error) {
    console.error('解析用户信息失败:', error)
    return null
  }
}

// 设置用户信息
export function setUserInfo(userInfo: any): void {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))
}

// 移除用户信息
export function removeUserInfo(): void {
  localStorage.removeItem(USER_INFO_KEY)
}

// 检查是否已登录
export function isAuthenticated(): boolean {
  return !!getToken()
}

// 检查令牌是否即将过期（在过期前5分钟）
export function isTokenExpiringSoon(): boolean {
  const token = getToken()
  if (!token) {
    return false
  }

  try {
    // JWT 令牌解析（简单实现，实际应该使用更安全的方法）
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp * 1000 // 转换为毫秒
    const now = Date.now()
    const fiveMinutes = 5 * 60 * 1000
    
    return exp - now < fiveMinutes
  } catch (error) {
    console.error('解析令牌失败:', error)
    return false
  }
}

// 获取令牌过期时间
export function getTokenExpiration(): Date | null {
  const token = getToken()
  if (!token) {
    return null
  }

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return new Date(payload.exp * 1000)
  } catch (error) {
    console.error('解析令牌过期时间失败:', error)
    return null
  }
}

// 登出
export function logout(): void {
  removeToken()
  removeUserInfo()
  // 清除所有相关的存储
  localStorage.clear()
  sessionStorage.clear()
  
  try {
    // 尝试清除 Cookies
    const cookies = document.cookie.split(';')
    for (const cookie of cookies) {
      const eqPos = cookie.indexOf('=')
      const name = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim()
      Cookies.remove(name)
    }
  } catch (error) {
    // Cookies 可能不可用，忽略错误
  }
}

// 验证令牌有效性
export async function validateToken(): Promise<boolean> {
  if (!isAuthenticated()) {
    return false
  }

  // 如果令牌即将过期，尝试刷新
  if (isTokenExpiringSoon()) {
    const refreshed = await refreshToken()
    if (!refreshed) {
      return false
    }
  }

  return true
}

// 初始化认证状态
export async function initAuth(): Promise<boolean> {
  if (!isAuthenticated()) {
    return false
  }

  // 验证令牌有效性
  const isValid = await validateToken()
  if (!isValid) {
    logout()
    return false
  }

  // 如果本地没有用户信息，尝试获取
  if (!getUserInfo()) {
    try {
      const userInfo = await authApi.getUserInfo()
      setUserInfo(userInfo)
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，可能是令牌无效
      logout()
      return false
    }
  }

  return true
}