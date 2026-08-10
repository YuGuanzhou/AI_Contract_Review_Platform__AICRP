// 管理员API接口
import { request } from './index'
import type {
  AdminOverview,
  MonitorData,
  SystemSettings,
  ManagedUser,
  BackupInfo,
  AuditLog,
  SystemLog,
  DataStatistics,
  AIModel
} from '@/types/admin'

// 获取系统概览
export const getOverview = (): Promise<{ data: AdminOverview }> => {
  return request.get('/api/admin/overview')
}

// 获取监控数据
export const getMonitorData = (): Promise<{ data: MonitorData }> => {
  return request.get('/api/admin/monitor')
}

// 获取系统设置
export const getSystemSettings = (): Promise<{ data: SystemSettings }> => {
  return request.get('/api/admin/settings')
}

// 更新系统设置
export const updateSystemSettings = (settings: Partial<SystemSettings>): Promise<{ data: { success: boolean; message: string } }> => {
  return request.put('/api/admin/settings', settings)
}

// 获取用户列表
export const getUsers = (params?: {
  page?: number
  page_size?: number
  search?: string
  role?: string
  is_active?: boolean
}): Promise<{
  items: ManagedUser[]
  total: number
  page: number
  page_size: number
}> => {
  return request.get('/admin/users', { params })
}

// 创建用户
export const createUser = (userData: {
  username: string
  email: string
  password: string
  full_name: string
  company?: string
  role: string
}): Promise<{ data: ManagedUser }> => {
  return request.post('/admin/users', userData)
}

// 更新用户
export const updateUser = (userId: number, userData: Partial<ManagedUser>): Promise<{ data: ManagedUser }> => {
  return request.put(`/admin/users/${userId}`, userData)
}

// 删除用户
export const deleteUser = (userId: number): Promise<{ data: { success: boolean; message: string } }> => {
  return request.delete(`/admin/users/${userId}`)
}

// 重置用户密码
export const resetUserPassword = (userId: number): Promise<{ data: { success: boolean; new_password?: string } }> => {
  return request.post(`/admin/users/${userId}/reset-password`)
}

// 获取备份列表
export const getBackups = (params?: {
  page?: number
  page_size?: number
}): Promise<{
  data: {
    items: BackupInfo[]
    total: number
  }
}> => {
  return request.get('/api/admin/backups', { params })
}

// 创建备份
export const createBackup = (backupData: {
  name: string
  type: 'full' | 'incremental'
  description?: string
}): Promise<{ data: BackupInfo }> => {
  return request.post('/api/admin/backups', backupData)
}

// 恢复备份
export const restoreBackup = (backupId: number): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post(`/api/admin/backups/${backupId}/restore`)
}

// 删除备份
export const deleteBackup = (backupId: number): Promise<{ data: { success: boolean; message: string } }> => {
  return request.delete(`/api/admin/backups/${backupId}`)
}

// 获取审计日志
export const getAuditLogs = (params?: {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  user_id?: number
  action?: string
}): Promise<{
  data: {
    items: AuditLog[]
    total: number
  }
}> => {
  return request.get('/api/admin/audit-logs', { params })
}

// 获取系统日志
export const getSystemLogs = (params?: {
  page?: number
  page_size?: number
  level?: string
  source?: string
  start_date?: string
  end_date?: string
}): Promise<{
  data: {
    items: SystemLog[]
    total: number
  }
}> => {
  return request.get('/api/admin/system-logs', { params })
}

// 清除日志
export const clearLogs = (logType: 'audit' | 'system' | 'all', daysToKeep?: number): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post('/api/admin/logs/clear', { log_type: logType, days_to_keep: daysToKeep })
}

// 获取数据统计
export const getDataStatistics = (params?: {
  start_date?: string
  end_date?: string
  interval?: 'day' | 'week' | 'month'
}): Promise<{ data: DataStatistics }> => {
  return request.get('/api/admin/statistics', { params })
}

// 获取AI模型列表
export const getAIModels = (): Promise<{ data: AIModel[] }> => {
  return request.get('/api/admin/ai-models')
}

// 更新AI模型
export const updateAIModel = (modelId: number, modelData: Partial<AIModel>): Promise<{ data: AIModel }> => {
  return request.put(`/api/admin/ai-models/${modelId}`, modelData)
}

// 训练AI模型
export const trainAIModel = (modelId: number, trainingData?: any): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post(`/api/admin/ai-models/${modelId}/train`, trainingData)
}

// 重启系统服务
export const restartServices = (serviceNames?: string[]): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post('/api/admin/services/restart', { services: serviceNames })
}

// 获取服务状态
export const getServiceStatus = (): Promise<{
  data: Array<{
    name: string
    status: string
    uptime: number
    health: number
  }>
}> => {
  return request.get('/api/admin/services/status')
}

// 发送系统通知
export const sendSystemNotification = (notificationData: {
  title: string
  message: string
  type: 'info' | 'warning' | 'error'
  target_users?: number[]
  target_roles?: string[]
}): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post('/api/admin/notifications', notificationData)
}

// 导出系统数据
export const exportSystemData = (params?: {
  data_type: 'users' | 'contracts' | 'reviews' | 'logs'
  format: 'excel' | 'csv' | 'json'
  start_date?: string
  end_date?: string
}): Promise<{ data: { download_url: string } }> => {
  return request.get('/api/admin/export', { params })
}

// 系统诊断
export const runSystemDiagnostics = (): Promise<{
  data: {
    checks: Array<{
      name: string
      status: 'pass' | 'fail' | 'warning'
      message: string
      details?: any
    }>
    overall_status: string
    recommendations: string[]
  }
}> => {
  return request.post('/api/admin/diagnostics')
}

export default {
  getOverview,
  getMonitorData,
  getSystemSettings,
  updateSystemSettings,
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  getBackups,
  createBackup,
  restoreBackup,
  deleteBackup,
  getAuditLogs,
  getSystemLogs,
  clearLogs,
  getDataStatistics,
  getAIModels,
  updateAIModel,
  trainAIModel,
  restartServices,
  getServiceStatus,
  sendSystemNotification,
  exportSystemData,
  runSystemDiagnostics
}