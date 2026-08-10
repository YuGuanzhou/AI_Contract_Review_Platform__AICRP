// 管理员相关类型定义

// 系统概览
export interface AdminOverview {
  total_users: number
  today_new_users: number
  user_counts: Record<string, number>
  total_contracts: number
  today_uploads: number
  contract_status: Record<string, number>
  total_reviews: number
  today_reviews: number
  ai_accuracy: number
  avg_review_time: number
  system_status?: string
  storage_usage?: number
}

// 系统监控数据
export interface MonitorData {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  api_requests: number
  database_connections: number
  queue_size: number
  response_time: number
  uptime: number
}

// 系统服务状态
export interface SystemService {
  name: string
  status: 'running' | 'stopped' | 'error'
  icon: string
  uptime?: number
  last_check?: string
  health?: number
}

// 系统告警
export interface SystemAlert {
  id: number
  level: 'high' | 'medium' | 'low'
  title: string
  description: string
  time: string
  service?: string
  resolved?: boolean
  resolved_at?: string
  resolved_by?: string
}

// 活动记录
export interface Activity {
  id: number
  type: 'user' | 'contract' | 'review' | 'system' | 'alert'
  icon: string
  title: string
  user: string
  time: string
  details?: Record<string, any>
}

// 用户管理
export interface ManagedUser {
  id: number
  username: string
  email: string
  full_name: string
  company: string
  role: 'user' | 'reviewer' | 'admin'
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login?: string
  contract_count: number
  review_count?: number
}

// 系统设置
export interface SystemSettings {
  general: {
    site_name: string
    site_description: string
    maintenance_mode: boolean
    registration_enabled: boolean
    default_user_role: string
  }
  ai: {
    model_name: string
    api_endpoint: string
    api_key: string
    confidence_threshold: number
    max_file_size: number
    supported_formats: string[]
  }
  review: {
    auto_assign_enabled: boolean
    max_pending_per_reviewer: number
    review_timeout_hours: number
    high_risk_threshold: number
    revision_allowed: boolean
  }
  storage: {
    max_storage_per_user: number
    cleanup_days: number
    backup_enabled: boolean
    backup_frequency: string
  }
  security: {
    password_min_length: number
    password_require_special: boolean
    session_timeout: number
    max_login_attempts: number
    ip_whitelist: string[]
  }
  notification: {
    email_enabled: boolean
    sms_enabled: boolean
    webhook_enabled: boolean
    contract_upload_notify: boolean
    review_complete_notify: boolean
    system_alert_notify: boolean
  }
}

// 备份信息
export interface BackupInfo {
  id: number
  name: string
  type: 'full' | 'incremental'
  size: number
  created_at: string
  status: 'completed' | 'failed' | 'in_progress'
  download_url?: string
  restore_point?: boolean
}

// 审计日志
export interface AuditLog {
  id: number
  user_id: number
  username: string
  action: string
  resource_type: string
  resource_id: number
  details: Record<string, any>
  ip_address: string
  user_agent: string
  created_at: string
}

// 系统日志
export interface SystemLog {
  id: number
  level: 'info' | 'warning' | 'error' | 'debug'
  source: string
  message: string
  timestamp: string
  details?: Record<string, any>
}

// 数据统计
export interface DataStatistics {
  time_range: {
    start: string
    end: string
  }
  user_growth: {
    date: string
    new_users: number
    active_users: number
  }[]
  contract_metrics: {
    date: string
    uploads: number
    reviews: number
    avg_risk_score: number
  }[]
  review_metrics: {
    date: string
    total_reviews: number
    avg_review_time: number
    ai_accuracy: number
    human_accuracy: number
  }[]
  system_metrics: {
    date: string
    cpu_usage: number
    memory_usage: number
    api_requests: number
    avg_response_time: number
  }[]
}

// AI模型信息
export interface AIModel {
  id: number
  name: string
  version: string
  type: 'contract_analysis' | 'risk_assessment' | 'clause_extraction'
  status: 'active' | 'training' | 'disabled'
  accuracy: number
  last_trained: string
  training_data_size: number
  supported_languages: string[]
  parameters: Record<string, any>
}

// 数据库统计
export interface DatabaseStats {
  tables: {
    name: string
    row_count: number
    size_mb: number
    last_updated: string
  }[]
  total_size_mb: number
  connection_count: number
  query_per_second: number
  cache_hit_rate: number
}