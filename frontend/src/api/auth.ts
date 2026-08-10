import { request } from './index'

// 用户登录接口
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: number
    username: string
    email: string
    full_name?: string
    company?: string
    role: string
    is_active: boolean
    is_verified: boolean
    created_at: string
  }
}

// 用户注册接口
export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
  company?: string
}

export interface RegisterResponse {
  id: number
  username: string
  email: string
  full_name?: string
  company?: string
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

// 刷新令牌接口
export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// 用户信息接口
export interface UserInfo {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  avatar?: string
  created_at: string
  updated_at: string
}

// 修改密码接口
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

// 更新用户信息接口
export interface UpdateUserInfoRequest {
  full_name?: string
  company?: string
  language?: string
  timezone?: string
}

// 更新用户角色接口
export interface UpdateUserRoleRequest {
  role: string
}

// 认证 API
export const authApi = {
  // 用户登录
  login(data: LoginRequest): Promise<LoginResponse> {
    return request.post('/auth/login', data)
  },

  // 用户注册
  register(data: RegisterRequest): Promise<RegisterResponse> {
    return request.post('/auth/register', data)
  },

  // 刷新令牌
  refreshToken(data: RefreshTokenRequest): Promise<RefreshTokenResponse> {
    return request.post('/auth/refresh', data)
  },

  // 获取用户信息
  getUserInfo(): Promise<UserInfo> {
    return request.get('/auth/me')
  },

  // 更新用户信息
  updateUserInfo(data: UpdateUserInfoRequest): Promise<UserInfo> {
    return request.put('/auth/me', data)
  },

  // 更新用户角色（仅管理员可用）
  updateUserRole(userId: number, data: UpdateUserRoleRequest): Promise<UserInfo> {
    return request.put(`/auth/users/${userId}/role`, data)
  },

  // 修改密码
  changePassword(data: ChangePasswordRequest): Promise<void> {
    return request.post('/auth/change-password', data)
  },

  // 退出登录
  logout(): Promise<void> {
    return request.post('/auth/logout')
  },

  // 发送重置密码邮件
  forgotPassword(email: string): Promise<{ message: string }> {
    return request.post('/auth/forgot-password', { email })
  },

  // 重置密码
  resetPassword(token: string, password: string, confirm_password: string): Promise<{ message: string }> {
    return request.post('/auth/reset-password', {
      token,
      password,
      confirm_password,
    })
  },

  // 验证重置密码令牌
  verifyResetToken(token: string): Promise<{ valid: boolean; email?: string }> {
    return request.get(`/auth/verify-reset-token/${token}`)
  },

  // 检查用户名是否可用
  checkUsernameAvailability(username: string): Promise<{ available: boolean }> {
    return request.get('/auth/check-username', { params: { username } })
  },

  // 检查邮箱是否可用
  checkEmailAvailability(email: string): Promise<{ available: boolean }> {
    return request.get('/auth/check-email', { params: { email } })
  },
}

export default authApi