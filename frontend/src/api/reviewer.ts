// 审核员API接口
import { request } from './index'
import type {
  ReviewerStats,
  PendingContract,
  ReviewRecord,
  ReviewActionRequest,
  ReviewDetail
} from '@/types/reviewer'

// 获取审核员统计信息
export const getReviewerStats = (): Promise<ReviewerStats> => {
  return request.get('/reviewer/stats')
}

// 获取待审核合同列表
export const getPendingContracts = (params?: {
  page?: number
  page_size?: number
  filter?: string
  sort_by?: string
}): Promise<{
  items: PendingContract[]
  total: number
  page: number
  page_size: number
}> => {
  return request.get('/reviewer/contracts/pending', { params })
}

// 获取审核记录
export const getReviewRecords = (params?: {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  reviewer_id?: number
}): Promise<{
  items: ReviewRecord[]
  total: number
}> => {
  return request.get('/reviewer/records', { params })
}

// 开始审核合同
export const startReview = (contractId: number): Promise<ReviewDetail> => {
  return request.post(`/reviewer/contracts/${contractId}/start-review`)
}

// 提交审核结果
export const submitReview = (data: ReviewActionRequest): Promise<{ success: boolean; message: string }> => {
  return request.post('/reviewer/review/submit', data)
}

// 获取审核详情
export const getReviewDetail = (reviewId: number): Promise<ReviewDetail> => {
  return request.get(`/reviewer/reviews/${reviewId}`)
}

// 批量审核通过
export const batchApproveContracts = (contractIds: number[]): Promise<{ success: boolean; message: string }> => {
  return request.post('/reviewer/batch/approve', { contract_ids: contractIds })
}

// 批量标记需修改
export const batchMarkRevision = (contractIds: number[], comments?: string): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post('/reviewer/batch/revision', { contract_ids: contractIds, comments })
}

// 批量拒绝合同
export const batchRejectContracts = (contractIds: number[], comments?: string): Promise<{ data: { success: boolean; message: string } }> => {
  return request.post('/reviewer/batch/reject', { contract_ids: contractIds, comments })
}

// 获取高风险合同
export const getHighRiskContracts = (params?: {
  page?: number
  page_size?: number
}): Promise<{
  data: {
    items: PendingContract[]
    total: number
  }
}> => {
  return request.get('/api/reviewer/contracts/high-risk', { params })
}

// 获取紧急合同
export const getUrgentContracts = (params?: {
  page?: number
  page_size?: number
}): Promise<{
  data: {
    items: PendingContract[]
    total: number
  }
}> => {
  return request.get('/api/reviewer/contracts/urgent', { params })
}

// 导出审核数据
export const exportReviewData = (params?: {
  start_date?: string
  end_date?: string
  format?: 'excel' | 'csv' | 'pdf'
}): Promise<{ data: { download_url: string } }> => {
  return request.get('/api/reviewer/export', { params })
}

// 获取审核效率统计
export const getReviewEfficiency = (params?: {
  start_date?: string
  end_date?: string
}): Promise<{
  data: {
    date: string
    total_reviews: number
    avg_review_time: number
    accuracy: number
  }[]
}> => {
  return request.get('/api/reviewer/efficiency', { params })
}

export default {
  getReviewerStats,
  getPendingContracts,
  getReviewRecords,
  startReview,
  submitReview,
  getReviewDetail,
  batchApproveContracts,
  batchMarkRevision,
  batchRejectContracts,
  getHighRiskContracts,
  getUrgentContracts,
  exportReviewData,
  getReviewEfficiency
}