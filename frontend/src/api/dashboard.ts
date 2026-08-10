/**
 * 仪表板相关 API
 */
import { request } from './index'

export interface DashboardStats {
  summary: {
    total_contracts: number
    total_reviews: number
    avg_risk_score: number
    high_risk_count: number
  }
  status_distribution: Record<string, number>
  type_distribution: Record<string, number>
  risk_distribution: Array<{
    risk_level: string
    count: number
    avg_score: number
  }>
  review_stats: {
    total_reviews: number
    ai_reviews: number
    manual_reviews: number
    finalized_reviews: number
  }
  recent_contracts: Array<{
    id: number
    title: string
    status: string
    risk_level: string
    uploaded_at: string
  }>
  high_risk_contracts: Array<{
    id: number
    title: string
    risk_score: number
    risk_level: string
    uploaded_at: string
  }>
  monthly_trend: Array<{
    month: string
    count: number
    avg_risk_score: number
  }>
}

export interface UserStats {
  contract_stats: {
    total: number
    reviewed: number
    parsed: number
    error: number
    avg_risk_score: number
  }
  review_stats: {
    total_reviews: number
    ai_reviews: number
    manual_reviews: number
  }
  recent_activities: Array<{
    id: number
    title: string
    action: string
    status: string
    timestamp: string
    risk_level: string
  }>
}

export interface AdminStats {
  user_distribution: Array<{
    role: string
    count: number
    latest_created: string
  }>
  system_overview: {
    total_users: number
    total_contracts: number
    total_reviews: number
    total_revisions: number
    avg_system_risk_score: number
    high_risk_contracts: number
    active_users: number
  }
  storage_usage: {
    total_storage_bytes: number
    total_storage_mb: number
    avg_file_size: number
    total_files: number
  }
}

/**
 * 获取仪表板统计信息
 */
export const getDashboardStats = async (): Promise<DashboardStats> => {
  return request.get('/stats/dashboard')
}

/**
 * 获取用户个人统计信息
 */
export const getUserStats = async (): Promise<UserStats> => {
  return request.get('/stats/user-stats')
}

/**
 * 获取管理员统计信息（仅管理员可访问）
 */
export const getAdminStats = async (): Promise<AdminStats> => {
  return request.get('/stats/admin/stats')
}

/**
 * 获取风险分布统计
 */
export const getRiskDistribution = async () => {
  return request.get('/contracts/stats/risk-distribution')
}

/**
 * 获取合同统计
 */
export const getContractStats = async (params?: {
  startDate?: string
  endDate?: string
  contractType?: string
}) => {
  return request.get('/contracts/stats', { params })
}

export default {
  getDashboardStats,
  getUserStats,
  getAdminStats,
  getRiskDistribution,
  getContractStats,
}