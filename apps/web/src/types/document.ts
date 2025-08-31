/**
 * 文檔管理相關類型定義
 */

// 文檔處理狀態
export type DocumentStatus =
  | 'queued'      // 排隊中
  | 'processing'  // 處理中
  | 'completed'   // 完成
  | 'failed'      // 失敗
  | 'cancelled'   // 取消

// 支援的檔案類型
export type SupportedFileType =
  | '.pdf'
  | '.docx'
  | '.pptx'
  | '.xlsx'
  | '.jpg'
  | '.jpeg'
  | '.png'
  | '.bmp'
  | '.tiff'
  | '.txt'

// 文檔元資料
export interface DocumentMetadata {
  document_id: string
  original_filename: string
  file_path: string
  file_size: number
  mime_type: string
  company_id: number
  created_by: string
  processing_status: string
  created_at: string
  updated_at: string
  error_message?: string
}

// 文檔上傳請求
export interface DocumentUploadRequest {
  file: File
  company_id: number
  category?: string
  description?: string
  tags?: string[]
}

// 文檔上傳回應
export interface DocumentUploadResponse {
  task_id: string
  status: DocumentStatus
  message: string
  document: DocumentMetadata
}

// 文檔處理狀態回應
export interface DocumentStatusResponse {
  id: string
  status: DocumentStatus
  progress: number
  message: string
  error?: string
  completed_at?: string
}

// 文檔列表查詢參數
export interface DocumentListParams extends Record<string, unknown> {
  company_id: number
  page?: number
  limit?: number
  status?: DocumentStatus
  category?: string
  search?: string
  sort_by?: 'created_at' | 'filename' | 'file_size' | 'status'
  sort_order?: 'asc' | 'desc'
}

// 文檔列表回應
export interface DocumentListResponse {
  company_id: number
  documents: DocumentMetadata[]
  total_count: number
}

// 批次操作類型
export type BatchAction = 'delete' | 'reprocess' | 'export' | 'update_category'

// 批次操作請求
export interface BatchOperationRequest {
  document_ids: string[]
  action: BatchAction
  params?: Record<string, unknown>
}

// 批次操作回應
export interface BatchOperationResponse {
  success: boolean
  message: string
  processed_count: number
  failed_count: number
  errors?: Array<{
    document_id: string
    error: string
  }>
}

// 文檔統計資訊
export interface DocumentStats {
  total_documents: number
  total_size: number
  documents_by_status: Record<string, number>
  documents_by_type: Record<string, number>
}

// 文檔上傳配置
export interface UploadConfig {
  max_file_size: number
  allowed_extensions: SupportedFileType[]
  max_files_per_batch: number
  concurrent_uploads: number
}

// 文檔搜尋結果
export interface DocumentSearchResult {
  document: DocumentMetadata
  relevance_score: number
  matched_content?: string
  highlights?: string[]
}

// 文檔搜尋回應
export interface DocumentSearchResponse {
  results: DocumentSearchResult[]
  total: number
  query: string
  took: number
}

// 文檔分類
export interface DocumentCategory {
  id: string
  name: string
  description?: string
  color?: string
  document_count: number
  created_at: string
}

// 文檔標籤
export interface DocumentTag {
  id: string
  name: string
  color?: string
  document_count: number
  created_at: string
}

// 上傳進度資訊
export interface UploadProgress {
  file_id: string
  filename: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
  uploaded_bytes: number
  total_bytes: number
  speed?: number
  eta?: number
}

// 文檔預覽資訊
export interface DocumentPreview {
  id: string
  preview_url?: string
  thumbnail_url?: string
  page_count?: number
  content_preview?: string
  extracted_text?: string
}

// 文檔版本資訊
export interface DocumentVersion {
  id: string
  document_id: string
  version: number
  filename: string
  file_size: number
  uploaded_by: number
  created_at: string
  is_current: boolean
  change_summary?: string
}

// 文檔權限
export interface DocumentPermission {
  document_id: string
  user_id?: number
  role?: string
  permissions: Array<'read' | 'write' | 'delete' | 'share'>
  granted_by: number
  granted_at: string
  expires_at?: string
}

// 文檔活動記錄
export interface DocumentActivity {
  id: string
  document_id: string
  user_id: number
  action: 'upload' | 'update' | 'delete' | 'download' | 'view' | 'share'
  details?: Record<string, unknown>
  ip_address?: string
  user_agent?: string
  created_at: string
}

// 文檔匯出選項
export interface DocumentExportOptions {
  format: 'pdf' | 'docx' | 'txt' | 'json'
  include_metadata: boolean
  include_content: boolean
  date_range?: {
    start: string
    end: string
  }
  categories?: string[]
  tags?: string[]
}

// 文檔匯出回應
export interface DocumentExportResponse {
  export_id: string
  status: 'preparing' | 'ready' | 'expired'
  download_url?: string
  file_size?: number
  expires_at: string
  created_at: string
}
