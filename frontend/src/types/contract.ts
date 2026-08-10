// 合同相关类型定义

// 用户合同
export interface UserContract {
  id: number
  contract_number: string
  title: string
  contract_type: string
  description?: string
  file_type: string
  file_size: number
  file_path: string
  status: 'pending' | 'reviewing' | 'approved' | 'revision' | 'rejected'
  rawStatus?: string
  risk_score?: number
  ai_findings_count?: number
  created_at: string
  updated_at: string
  reviewed_at?: string
  reviewer?: string
  reviewer_contact?: string
  is_urgent?: boolean
  review_comments?: string
}

// 合同统计
export interface ContractStats {
  total_contracts?: number
  pending_reviews?: number
  approved_contracts?: number
  high_risk_contracts?: number
  today_uploads?: number
  avg_risk_score?: number
  by_type?: Record<string, number>
  by_status?: Record<string, number>
}

// 合同详情
export interface ContractDetail {
  id: number
  contract_number: string
  title: string
  contract_type: string
  description?: string
  file_info: {
    type: string
    size: number
    path: string
    original_name: string
    upload_time: string
  }
  uploader: {
    id: number
    username: string
    full_name: string
    company: string
    email: string
  }
  status: {
    current: string
    history: StatusHistory[]
  }
  risk_assessment: {
    score: number
    level: 'low' | 'medium' | 'high'
    factors: RiskFactor[]
    summary: string
  }
  ai_review?: {
    findings: AIFinding[]
    confidence: number
    processing_time: number
    model_version: string
  }
  human_review?: {
    reviewer: string
    review_time: string
    status: string
    comments: string
    findings: HumanFinding[]
  }
  metadata?: Record<string, any>
}

// 状态历史
export interface StatusHistory {
  status: string
  changed_at: string
  changed_by: string
  comments?: string
}

// 风险因素
export interface RiskFactor {
  type: string
  severity: 'low' | 'medium' | 'high'
  description: string
  clause_reference?: string
  page_number?: number
  confidence: number
}

// AI发现问题
export interface AIFinding {
  id: number
  type: 'risk' | 'clause' | 'compliance' | 'format' | 'other'
  severity: 'low' | 'medium' | 'high'
  description: string
  suggestion: string
  confidence: number
  clause_reference?: string
  page_number?: number
  line_number?: number
}

// 人工发现问题
export interface HumanFinding {
  id: number
  type: 'risk' | 'clause' | 'compliance' | 'format' | 'other'
  severity: 'low' | 'medium' | 'high'
  description: string
  suggestion: string
  clause_reference?: string
  page_number?: number
  agreed_with_ai: boolean
  ai_finding_id?: number
}

// 合同上传表单
export interface ContractUploadForm {
  title: string
  contract_type: string
  description?: string
  file: File | null
  auto_review: boolean
  notify_on_complete: boolean
  tags?: string[]
}

// 合同搜索参数
export interface ContractSearchParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  risk_level?: string
  contract_type?: string
  start_date?: string
  end_date?: string
  sort_field?: string
  sort_order?: 'asc' | 'desc'
  uploader_id?: number
}

// 合同搜索响应
export interface ContractSearchResponse {
  items?: UserContract[]  // 前端期望的字段
  contracts?: UserContract[]  // 后端实际返回的字段
  total: number
  page?: number
  page_size?: number
  total_pages?: number
  skip?: number  // 后端实际返回的字段
  limit?: number  // 后端实际返回的字段
}

// 合同审核请求
export interface ContractReviewRequest {
  contract_id: number
  action: 'approve' | 'revision' | 'reject'
  comments: string
  findings?: HumanFinding[]
  risk_score?: number
  notify_user: boolean
}

// 合同批量操作
export interface ContractBatchOperation {
  contract_ids: number[]
  action: 'delete' | 'export' | 'change_status'
  parameters?: Record<string, any>
}

// 合同模板
export interface ContractTemplate {
  id: number
  name: string
  description?: string
  type: string
  content: string
  variables: TemplateVariable[]
  created_at: string
  updated_at: string
  created_by: string
  is_active: boolean
  usage_count: number
}

// 模板变量
export interface TemplateVariable {
  name: string
  type: 'text' | 'number' | 'date' | 'select' | 'boolean'
  label: string
  required: boolean
  default_value?: any
  options?: string[]
  validation_rules?: string[]
}

// 合同导出选项
export interface ExportOptions {
  format: 'pdf' | 'excel' | 'csv' | 'json'
  include_fields: string[]
  include_reviews: boolean
  include_ai_findings: boolean
  include_human_findings: boolean
  time_range?: {
    start: string
    end: string
  }
}