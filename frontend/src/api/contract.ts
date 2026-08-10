import { request } from './index'

// 合同类型
export interface Contract {
  id: number
  user_id: number
  title: string
  description: string | null
  contract_type: string
  status: string
  original_filename: string
  file_path: string | null
  file_size: number | null
  file_type: string | null
  file_hash: string | null
  parsed_text: string | null
  parsed_json: any | null
  page_count: number | null
  word_count: number | null
  risk_level: string | null
  risk_score: number | null
  review_summary: string | null
  uploaded_at: string
  parsed_at: string | null
  reviewed_at: string | null
  archived_at: string | null
}

// 合同列表响应
export interface ContractListResponse {
  contracts: Contract[]
  total: number
  skip: number
  limit: number
}

// 合同上传响应
export interface ContractUploadResponse {
  contract: Contract
  message: string
}

// 获取合同列表
export const getContracts = async (
  skip: number = 0,
  limit: number = 10,
  status?: string,
  contract_type?: string,
  search?: string,
  user_id?: number
): Promise<ContractListResponse> => {
  const params: any = { skip, limit }
  if (status) params.status = status
  if (contract_type) params.contract_type = contract_type
  if (search) params.search = search
  if (user_id !== undefined) params.user_id = user_id
  
  return request.get<ContractListResponse>('/contracts/', { params })
}

// 获取单个合同
export const getContract = async (id: number): Promise<Contract> => {
  return request.get<Contract>(`/contracts/${id}`)
}

// 上传合同
export const uploadContract = async (
  formData: FormData
): Promise<ContractUploadResponse> => {
  return request.upload<ContractUploadResponse>('/contracts/upload', formData)
}

// 更新合同
export const updateContract = async (
  id: number,
  data: Partial<Contract>
): Promise<Contract> => {
  return request.put<Contract>(`/contracts/${id}`, data)
}

// 删除合同
export const deleteContract = async (id: number): Promise<void> => {
  return request.delete(`/contracts/${id}`)
}

// 下载合同文件
export const downloadContract = async (id: number): Promise<Blob> => {
  return request.get(`/contracts/${id}/download`, {
    responseType: 'blob'
  })
}

// 合同AI审核详情响应
export interface ContractReviewDetails {
  success: boolean
  contract_id: number
  status: string
  risk_score: number
  risk_level: string
  review_summary: string | null
  has_ai_review: boolean
  ai_review_result: any | null
  risk_points: any[]
  suggestions: any
  reviewed_at: string | null
}

// 提交人工审核请求体
export interface SubmitReviewPayload {
  manual_review_result: Record<string, any>
  risk_points?: any[]
  suggestions?: any
  risk_score?: number
  risk_level?: string
  review_summary?: string
}

// 解析合同
export const parseContract = async (id: number): Promise<any> => {
  return request.post(`/contracts/${id}/parse`)
}

// 获取合同审核详情（含 AI 审核结果与风险点）
export const getContractReviewDetails = async (id: number): Promise<ContractReviewDetails> => {
  return request.get<ContractReviewDetails>(`/contracts/${id}/review-details`)
}

// 触发/重跑 AI 审核
export const triggerAiReview = async (id: number): Promise<any> => {
  return request.post(`/contracts/${id}/trigger-ai-review`)
}

// 提交人工审核结果
export const submitContractReview = async (id: number, data: SubmitReviewPayload): Promise<any> => {
  return request.post(`/contracts/${id}/review`, data)
}

// 导入用户合同API
import userContractApi from './userContract'

// 组合合同API对象
export const contractApi = {
  // 来自当前模块的方法
  getContracts,
  getContract,
  uploadContract,
  updateContract,
  deleteContract,
  downloadContract,
  parseContract,
  getContractReviewDetails,
  triggerAiReview,
  submitContractReview,
  
  // 来自userContract模块的方法
  getUserStats: userContractApi.getUserStats,
  getUserContracts: userContractApi.getUserContracts,
  getContractDetail: userContractApi.getContractDetail,
  deleteUserContract: userContractApi.deleteUserContract,
  reuploadContract: userContractApi.reuploadContract,
  getReviewProgress: userContractApi.getReviewProgress,
  getContractNotifications: userContractApi.getContractNotifications,
  markNotificationAsRead: userContractApi.markNotificationAsRead,
  exportUserContracts: userContractApi.exportUserContracts,
  batchUserContractAction: userContractApi.batchUserContractAction,
  getShareLink: userContractApi.getShareLink,
  revokeShareLink: userContractApi.revokeShareLink,
  getContractComments: userContractApi.getContractComments,
  addContractComment: userContractApi.addContractComment,
  deleteContractComment: userContractApi.deleteContractComment,
  getContractVersions: userContractApi.getContractVersions,
  restoreContractVersion: userContractApi.restoreContractVersion
}