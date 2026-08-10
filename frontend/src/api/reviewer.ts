// 审核员API接口
import { request } from './index'
import type { ReviewerStats, PendingContract } from '@/types/reviewer'

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

// 开始审核合同（触发 AI 审核并进入人工审核流程）
export const startReview = (contractId: number): Promise<any> => {
  return request.post(`/reviewer/contracts/${contractId}/start-review`)
}

export default {
  getReviewerStats,
  getPendingContracts,
  startReview
}
