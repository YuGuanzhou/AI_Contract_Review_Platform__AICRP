// 审核员相关类型定义

// 审核员统计信息
export interface ReviewerStats {
  pending_reviews?: number
  urgent_pending?: number
  today_reviews?: number
  avg_review_time?: number
  review_accuracy?: number
  ai_accuracy?: number
  high_risk_pending?: number
  today_approved?: number
  today_revision?: number
  today_rejected?: number
}

// 待审核合同
export interface PendingContract {
  id: number
  contract_number: string
  contract_name: string
  file_type: string
  file_size: number
  uploader: string
  uploader_company: string
  risk_score: number
  ai_findings_count: number
  created_at: string
  waiting_hours: number
  is_urgent?: boolean
  assigned_to?: string
  contract_type?: string
}

// 审核员信息
export interface Reviewer {
  id: number
  name: string
  username: string
  pending_count: number
  workload: number
  email?: string
  phone?: string
  is_active?: boolean
}

// 审核记录
export interface ReviewRecord {
  id: number
  contract_id: number
  contract_number: string
  contract_name: string
  reviewer_id: number
  reviewer_name: string
  review_status: 'approved' | 'revision' | 'rejected' | 'pending'
  review_result?: string
  risk_score: number
  ai_findings_count: number
  human_findings_count: number
  review_time: number // 分钟
  created_at: string
  completed_at?: string
}

// 批量分配请求
export interface BatchAssignRequest {
  contract_ids: number[]
  reviewer_id: number
  notes?: string
  priority: 'normal' | 'high' | 'urgent'
}

// 审核操作请求
export interface ReviewActionRequest {
  contract_id: number
  action: 'approve' | 'revision' | 'reject'
  comments?: string
  findings?: ReviewFinding[]
}

// 审核发现问题
export interface ReviewFinding {
  id?: number
  type: 'risk' | 'clause' | 'compliance' | 'other'
  severity: 'high' | 'medium' | 'low'
  description: string
  suggestion?: string
  clause_reference?: string
  page_number?: number
}

// 审核详情
export interface ReviewDetail {
  id: number
  contract_id: number
  contract_info: {
    title: string
    contract_number: string
    uploader: string
    upload_time: string
    file_type: string
    file_size: number
  }
  ai_review: {
    risk_score: number
    findings: AIFinding[]
    summary: string
    confidence: number
  }
  human_review?: {
    reviewer: string
    review_time: string
    status: string
    comments: string
    findings: ReviewFinding[]
  }
  comparison?: {
    ai_accuracy: number
    human_agreement: boolean
    differences: string[]
  }
}

// AI发现问题
export interface AIFinding {
  id: number
  type: string
  severity: 'high' | 'medium' | 'low'
  description: string
  suggestion: string
  confidence: number
  clause_reference?: string
  page_number?: number
}

// 审核员工作负载
export interface ReviewerWorkload {
  reviewer_id: number
  reviewer_name: string
  pending_count: number
  today_reviews: number
  avg_review_time: number
  workload_percentage: number
  last_active: string
}