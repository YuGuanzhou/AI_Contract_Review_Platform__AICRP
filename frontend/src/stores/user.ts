import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/api/auth'
import { authApi } from '@/api/auth'
import { setToken, getToken, removeToken } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref<UserInfo | null>(null)
  const token = ref<string | null>(getToken())
  const permissions = ref<string[]>([])

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!userInfo.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const userName = computed(() => userInfo.value?.username || '')
  const userRole = computed(() => userInfo.value?.role || '')
  const userFullName = computed(() => userInfo.value?.full_name || userInfo.value?.username || '')

  // 登录
  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login({ username, password })
      
      // 保存 token 和用户信息
      token.value = response.access_token
      userInfo.value = response.user
      
      // 保存到本地存储
      setToken(response.access_token, response.refresh_token)
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  // 注册
  const register = async (userData: any) => {
    try {
      const response = await authApi.register(userData)
      return response
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }

  // 登出
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      // 清除本地状态
      token.value = null
      userInfo.value = null
      permissions.value = []
      
      // 清除本地存储
      removeToken()
    }
  }

  // 刷新 token
  const refreshToken = async () => {
    try {
      const response = await authApi.refreshToken()
      token.value = response.access_token
      setToken(response.access_token, response.refresh_token)
      return response
    } catch (error) {
      console.error('刷新 token 失败:', error)
      throw error
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const response = await authApi.getUserInfo()
      userInfo.value = response
      return response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  // 更新用户信息
  const updateUserInfo = async (userData: any) => {
    try {
      const response = await authApi.updateUserInfo(userData)
      userInfo.value = response
      return response
    } catch (error) {
      console.error('更新用户信息失败:', error)
      throw error
    }
  }

  // 修改密码
  const changePassword = async (passwordData: any) => {
    try {
      await authApi.changePassword(passwordData)
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  }

  // 检查认证状态
  const checkAuth = async () => {
    const localToken = getToken()
    if (!localToken) {
      return false
    }
    
    try {
      token.value = localToken
      await fetchUserInfo()
      return true
    } catch (error) {
      console.error('检查认证状态失败:', error)
      token.value = null
      userInfo.value = null
      removeToken()
      return false
    }
  }

  // 重置状态
  const reset = () => {
    token.value = null
    userInfo.value = null
    permissions.value = []
    removeToken()
  }

  return {
    // 状态
    userInfo,
    token,
    permissions,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    userName,
    userRole,
    userFullName,
    
    // 方法
    login,
    register,
    logout,
    refreshToken,
    fetchUserInfo,
    updateUserInfo,
    changePassword,
    checkAuth,
    reset,
  }
})