/**
 * 公司管理相關類型定義
 */

// 公司基本資訊 (匹配後端模型)
export interface Company {
  id: number
  name: string
  code: string
  line_channel_token?: string
  line_channel_secret?: string
  line_bot_enabled: boolean
  subscription_plan: string
  max_documents: number
  max_queries_per_month: number
  rag_working_dir?: string
  storage_quota_gb: number
  created_at: string
  updated_at?: string
  is_active: boolean
  // 前端擴展欄位
  description?: string
  website?: string
  phone?: string
  email?: string
  address?: string
  logo_url?: string
  settings?: CompanySettings
  stats?: CompanyStats
}

// 公司設定
export interface CompanySettings {
  // LINE Bot 設定
  line_bot_enabled: boolean
  line_channel_access_token?: string
  line_channel_secret?: string
  line_webhook_url?: string

  // AI 設定
  ai_model?: string
  ai_temperature?: number
  ai_max_tokens?: number

  // 知識庫設定
  knowledge_base_enabled: boolean
  max_documents?: number
  max_document_size?: number
  allowed_file_types?: string[]

  // 其他設定
  timezone?: string
  language?: string
  business_hours?: BusinessHours[]
}

// 營業時間
export interface BusinessHours {
  day: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
  start_time: string // HH:mm 格式
  end_time: string   // HH:mm 格式
  is_enabled: boolean
}

// 公司統計資訊
export interface CompanyStats {
  total_users: number
  active_users: number
  total_documents: number
  total_conversations: number
  monthly_conversations: number
  storage_used: number // bytes
  storage_limit: number // bytes
  last_activity?: string
}

// 建立公司請求
export interface CreateCompanyRequest {
  name: string
  description?: string
  website?: string
  phone?: string
  email?: string
  address?: string
  settings?: Partial<CompanySettings>
}

// 更新公司請求
export interface UpdateCompanyRequest {
  name?: string
  description?: string
  website?: string
  phone?: string
  email?: string
  address?: string
  is_active?: boolean
  settings?: Partial<CompanySettings>
}

// 公司列表查詢參數
export interface CompanyListParams {
  page?: number
  limit?: number
  search?: string
  is_active?: boolean
  sort_by?: 'name' | 'created_at' | 'updated_at' | 'total_users'
  sort_order?: 'asc' | 'desc'
}

// 公司列表回應
export interface CompanyListResponse {
  companies: Company[]
  total: number
  page: number
  limit: number
  has_next: boolean
  has_prev: boolean
}

// 公司用戶
export interface CompanyUser {
  id: number
  email: string
  name: string
  role: 'company_admin' | 'cs_manager' | 'cs_agent'
  is_active: boolean
  created_at: string
  last_login?: string
  permissions?: string[]
}

// 公司用戶列表
export interface CompanyUserListResponse {
  users: CompanyUser[]
  total: number
  page: number
  limit: number
}

// 邀請用戶請求
export interface InviteUserRequest {
  email: string
  name: string
  role: 'company_admin' | 'cs_manager' | 'cs_agent'
  permissions?: string[]
}

// 公司邀請
export interface CompanyInvitation {
  id: string
  company_id: string
  email: string
  name: string
  role: string
  invited_by: number
  invited_at: string
  expires_at: string
  is_accepted: boolean
  accepted_at?: string
}

// 公司活動記錄
export interface CompanyActivity {
  id: string
  company_id: string
  user_id?: number
  action: 'created' | 'updated' | 'activated' | 'deactivated' | 'user_invited' | 'user_joined' | 'settings_changed'
  details?: Record<string, unknown>
  ip_address?: string
  user_agent?: string
  created_at: string
}

// 公司配額
export interface CompanyQuota {
  max_users: number
  max_documents: number
  max_storage: number // bytes
  max_conversations_per_month: number
  features: string[]
}

// 公司計費資訊
export interface CompanyBilling {
  plan: 'free' | 'basic' | 'pro' | 'enterprise'
  billing_cycle: 'monthly' | 'yearly'
  next_billing_date?: string
  amount?: number
  currency?: string
  payment_method?: string
  quota: CompanyQuota
}

// 公司整合設定
export interface CompanyIntegration {
  id: string
  company_id: string
  type: 'line' | 'webhook' | 'api'
  name: string
  config: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
  last_sync?: string
  sync_status?: 'success' | 'error' | 'pending'
  error_message?: string
}

// 公司範本
export interface CompanyTemplate {
  id: string
  name: string
  description: string
  settings: CompanySettings
  is_default: boolean
  created_at: string
}

// 公司匯出選項
export interface CompanyExportOptions {
  format: 'csv' | 'xlsx' | 'json'
  include_users: boolean
  include_stats: boolean
  include_settings: boolean
  date_range?: {
    start: string
    end: string
  }
}

// 公司匯入選項
export interface CompanyImportOptions {
  format: 'csv' | 'xlsx' | 'json'
  update_existing: boolean
  skip_duplicates: boolean
  default_settings?: Partial<CompanySettings>
}

// 公司驗證規則
export interface CompanyValidation {
  name: {
    required: boolean
    min_length: number
    max_length: number
    pattern?: string
  }
  email: {
    required: boolean
    pattern: string
  }
  phone: {
    required: boolean
    pattern?: string
  }
}

// 公司搜尋結果
export interface CompanySearchResult {
  company: Company
  relevance_score: number
  matched_fields: string[]
  highlights?: Record<string, string[]>
}

// 公司搜尋回應
export interface CompanySearchResponse {
  results: CompanySearchResult[]
  total: number
  query: string
  took: number
}

// 公司狀態
export type CompanyStatus = 'active' | 'inactive' | 'suspended' | 'pending'

// 公司類型
export type CompanyType = 'enterprise' | 'small_business' | 'startup' | 'individual'

// 公司規模
export type CompanySize = '1-10' | '11-50' | '51-200' | '201-1000' | '1000+'

// LINE 設定更新請求
export interface LineSettingsUpdateRequest {
  line_channel_token: string
  line_channel_secret: string
  line_bot_enabled: boolean
}

// LINE 連線測試結果
export interface LineConnectionTestResult {
  success: boolean
  message: string
  webhook_url?: string
  channel_info?: {
    channel_id: string
    channel_name: string
    channel_description?: string
  }
}
