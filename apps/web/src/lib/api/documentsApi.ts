/**
 * 文檔管理 API
 */

import { httpClient } from './httpClient'
import type {
  DocumentUploadResponse,
  DocumentStatusResponse,
  DocumentListResponse,
} from '@/types/document'

export const documentsApi = {
  /**
   * 上傳文檔
   */
  upload: (formData: FormData): Promise<DocumentUploadResponse> =>
    httpClient.post('/api/ingest/document', formData),

  /**
   * 獲取文檔狀態
   */
  getStatus: (taskId: string): Promise<DocumentStatusResponse> =>
    httpClient.get(`/api/ingest/status/${taskId}`),

  /**
   * 獲取公司文檔列表
   */
  getCompanyDocuments: (companyId: number, params?: {
    skip?: number
    limit?: number
  }): Promise<DocumentListResponse> =>
    httpClient.get(`/api/ingest/documents/${companyId}`, params),

  /**
   * 刪除文檔
   */
  delete: (documentId: string): Promise<{ message: string }> =>
    httpClient.delete(`/api/ingest/document/${documentId}`),

  /**
   * 獲取文檔統計
   */
  getStats: (companyId: number): Promise<{
    total_documents: number
    total_size: number
    documents_by_status: Record<string, number>
    documents_by_type: Record<string, number>
  }> =>
    httpClient.get(`/api/ingest/documents/${companyId}`),

  /**
   * 搜尋文檔
   */
  search: (companyId: number, query: string, limit?: number): Promise<{
    documents: Array<{
      id: string
      filename: string
      relevance_score: number
      snippet: string
    }>
    total: number
  }> =>
    httpClient.get(`/api/documents/company/${companyId}/search`, { q: query, limit }),
}