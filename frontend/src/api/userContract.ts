// 用户合同API接口
import { request } from './index'
import type {
  UserContract,
  ContractStats,
  ContractSearchParams,
  ContractSearchResponse,
  ContractDetail
} from '../types/contract'

// 获取用户合同统计
export const getUserStats = (): Promise<ContractStats> => {
  return request.get('/user/contracts/stats')
}

// 获取用户合同列表
export const getUserContracts = (params?: ContractSearchParams): Promise<ContractSearchResponse> => {
  return request.get('/user/contracts', { params })
}

// 获取合同详情
export const getContractDetail = (contractId: number): Promise<{ data: ContractDetail }> => {
  return request.get(`/user/contracts/${contractId}`)
}

// 删除用户合同
export const deleteUserContract = (contractId: number): Promise<{ data: { success: boolean; message: string } }> => {
  return request.delete(`/user/contracts/${contractId}`)
}

// 重新上传合同
export const reuploadContract = (contractId: number, formData: FormData): Promise<{ data: UserContract }> => {
  return request.post(`/user/contracts/${contractId}/reupload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取合同审核进度
export const getReviewProgress = (contractId: number): Promise<{
  data: {
    status: string
    current_step: string
    progress_percentage: number
    estimated_completion?: string
    reviewer?: string
    last_update: string
    steps: Array<{
      name: string
      status: 'pending' | 'in_progress' | 'completed' | 'failed'
      completed_at?: string
      details?: string
    }>
  }
}> => {
  return request.get(`/user/contracts/${contractId}/review-progress`)
}

// 获取合同通知
export const getContractNotifications = (contractId: number): Promise<{
  data: Array<{
    id: number
    type: 'review' | 'comment' | 'status_change' | 'reminder'
    title: string
    message: string
    created_at: string
    read: boolean
    action_url?: string
  }>
}> => {
  return request.get(`/user/contracts/${contractId}/notifications`)
}

// 标记通知为已读
export const markNotificationAsRead = (notificationId: number): Promise<{ data: { success: boolean } }> => {
  return request.put(`/user/notifications/${notificationId}/read`)
}

// 导出用户合同
export const exportUserContracts = (params?: {
  format: 'excel' | 'csv' | 'pdf'
  include_fields: string[]
  start_date?: string
  end_date?: string
}): Promise<{ data: { download_url: string } }> => {
  return request.get('/user/contracts/export', { params })
}

// 批量操作用户合同
export const batchUserContractAction = (data: {
  contract_ids: number[]
  action: 'delete' | 'export' | 'archive'
  parameters?: Record<string, any>
}): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post('/user/contracts/batch', data)
}

// 获取合同分享链接
export const getShareLink = (contractId: number, options?: {
  expires_in?: number // 小时
  password_protected?: boolean
  view_only?: boolean
}): Promise<{ data: { share_url: string; expires_at: string; access_code?: string } }> => {
  return request.post(`/user/contracts/${contractId}/share`, options)
}

// 撤销分享链接
export const revokeShareLink = (contractId: number, shareId: number): Promise<{ data: { success: boolean } }> => {
  return request.delete(`/user/contracts/${contractId}/share/${shareId}`)
}

// 获取合同评论
export const getContractComments = (contractId: number): Promise<{
  data: Array<{
    id: number
    user_id: number
    username: string
    avatar?: string
    content: string
    created_at: string
    is_owner: boolean
    replies?: Array<{
      id: number
      user_id: number
      username: string
      content: string
      created_at: string
    }>
  }>
}> => {
  return request.get(`/user/contracts/${contractId}/comments`)
}

// 添加合同评论
export const addContractComment = (contractId: number, content: string): Promise<{
  data: {
    id: number
    content: string
    created_at: string
  }
}> => {
  return request.post(`/user/contracts/${contractId}/comments`, { content })
}

// 删除合同评论
export const deleteContractComment = (contractId: number, commentId: number): Promise<{ data: { success: boolean } }> => {
  return request.delete(`/user/contracts/${contractId}/comments/${commentId}`)
}

// 获取合同版本历史
export const getContractVersions = (contractId: number): Promise<{
  data: Array<{
    version: number
    created_at: string
    file_size: number
    changes: string[]
    uploaded_by: string
    download_url: string
  }>
}> => {
  return request.get(`/user/contracts/${contractId}/versions`)
}

// 恢复到指定版本
export const restoreContractVersion = (contractId: number, version: number): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post(`/user/contracts/${contractId}/versions/${version}/restore`)
}

export default {
  getUserStats,
  getUserContracts,
  getContractDetail,
  deleteUserContract,
  reuploadContract,
  getReviewProgress,
  getContractNotifications,
  markNotificationAsRead,
  exportUserContracts,
  batchUserContractAction,
  getShareLink,
  revokeShareLink,
  getContractComments,
  addContractComment,
  deleteContractComment,
  getContractVersions,
  restoreContractVersion
}