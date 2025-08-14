/**
 * 文檔管理 API 客戶端
 */

import { apiClient } from './client'
import type {
  DocumentMetadata,
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentStatusResponse,
  DocumentListParams,
  DocumentListResponse,
  BatchOperationRequest,
  BatchOperationResponse,
  DocumentStats,
  DocumentSearchResponse,
  DocumentCategory,
  DocumentTag,
  DocumentExportOptions,
  DocumentExportResponse,
  UploadConfig,
} from '@/types/document'

export class DocumentsApi {
  /**
   * 上傳單個文檔
   */
  async uploadDocument(request: DocumentUploadRequest): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', request.file)
    formData.append('company_id', request.company_id.toString())

    if (request.category) {
      formData.append('category', request.category)
    }

    if (request.description) {
      formData.append('description', request.description)
    }

    if (request.tags && request.tags.length > 0) {
      formData.append('tags', JSON.stringify(request.tags))
    }

    return apiClient.request<DocumentUploadResponse>('/ingest/document', {
      method: 'POST',
      body: formData,
      headers: {
        // 不設定 Content-Type，讓瀏覽器自動設定 multipart/form-data
      },
    })
  }

  /**
   * 批次上傳文檔
   */
  async uploadDocuments(files: File[], companyId: number, options?: {
    category?: string
    description?: string
    tags?: string[]
  }): Promise<DocumentUploadResponse[]> {
    const uploadPromises = files.map(file =>
      this.uploadDocument({
        file,
        company_id: companyId,
        category: options?.category,
        description: options?.description,
        tags: options?.tags,
      })
    )

    return Promise.all(uploadPromises)
  }

  /**
   * 查詢文檔處理狀態
   */
  async getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
    return apiClient.get<DocumentStatusResponse>(`/documents/${documentId}/status`)
  }

  /**
   * 獲取文檔列表
   */
  async getDocuments(params: DocumentListParams): Promise<DocumentListResponse> {
    return apiClient.get<DocumentListResponse>('/documents', params)
  }

  /**
   * 獲取單個文檔詳情
   */
  async getDocument(documentId: string): Promise<DocumentMetadata> {
    return apiClient.get<DocumentMetadata>(`/documents/${documentId}`)
  }

  /**
   * 更新文檔資訊
   */
  async updateDocument(
    documentId: string,
    updates: Partial<Pick<DocumentMetadata, 'category' | 'description' | 'tags'>>
  ): Promise<DocumentMetadata> {
    return apiClient.put<DocumentMetadata>(`/documents/${documentId}`, updates)
  }

  /**
   * 刪除文檔
   */
  async deleteDocument(documentId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/documents/${documentId}`)
  }

  /**
   * 批次操作文檔
   */
  async batchOperation(request: BatchOperationRequest): Promise<BatchOperationResponse> {
    return apiClient.post<BatchOperationResponse>('/documents/batch', request)
  }

  /**
   * 重新處理文檔
   */
  async reprocessDocument(documentId: string): Promise<DocumentStatusResponse> {
    return apiClient.post<DocumentStatusResponse>(`/documents/${documentId}/reprocess`)
  }

  /**
   * 獲取文檔統計資訊
   */
  async getDocumentStats(companyId: number): Promise<DocumentStats> {
    return apiClient.get<DocumentStats>('/documents/stats', { company_id: companyId })
  }

  /**
   * 搜尋文檔
   */
  async searchDocuments(
    query: string,
    companyId: number,
    options?: {
      limit?: number
      categories?: string[]
      tags?: string[]
      file_types?: string[]
    }
  ): Promise<DocumentSearchResponse> {
    return apiClient.post<DocumentSearchResponse>('/documents/search', {
      query,
      company_id: companyId,
      ...options,
    })
  }

  /**
   * 獲取文檔分類列表
   */
  async getCategories(companyId: number): Promise<DocumentCategory[]> {
    return apiClient.get<DocumentCategory[]>('/documents/categories', { company_id: companyId })
  }

  /**
   * 建立文檔分類
   */
  async createCategory(companyId: number, category: {
    name: string
    description?: string
    color?: string
  }): Promise<DocumentCategory> {
    return apiClient.post<DocumentCategory>('/documents/categories', {
      ...category,
      company_id: companyId,
    })
  }

  /**
   * 更新文檔分類
   */
  async updateCategory(categoryId: string, updates: {
    name?: string
    description?: string
    color?: string
  }): Promise<DocumentCategory> {
    return apiClient.put<DocumentCategory>(`/documents/categories/${categoryId}`, updates)
  }

  /**
   * 刪除文檔分類
   */
  async deleteCategory(categoryId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/documents/categories/${categoryId}`)
  }

  /**
   * 獲取文檔標籤列表
   */
  async getTags(companyId: number): Promise<DocumentTag[]> {
    return apiClient.get<DocumentTag[]>('/documents/tags', { company_id: companyId })
  }

  /**
   * 建立文檔標籤
   */
  async createTag(companyId: number, tag: {
    name: string
    color?: string
  }): Promise<DocumentTag> {
    return apiClient.post<DocumentTag>('/documents/tags', {
      ...tag,
      company_id: companyId,
    })
  }

  /**
   * 刪除文檔標籤
   */
  async deleteTag(tagId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/documents/tags/${tagId}`)
  }

  /**
   * 匯出文檔
   */
  async exportDocuments(
    companyId: number,
    options: DocumentExportOptions
  ): Promise<DocumentExportResponse> {
    return apiClient.post<DocumentExportResponse>('/documents/export', {
      company_id: companyId,
      ...options,
    })
  }

  /**
   * 獲取匯出狀態
   */
  async getExportStatus(exportId: string): Promise<DocumentExportResponse> {
    return apiClient.get<DocumentExportResponse>(`/documents/exports/${exportId}`)
  }

  /**
   * 下載文檔
   */
  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await apiClient.request<Blob>(`/documents/${documentId}/download`, {
      method: 'GET',
    })
    return response
  }

  /**
   * 獲取上傳配置
   */
  async getUploadConfig(): Promise<UploadConfig> {
    return apiClient.get<UploadConfig>('/documents/config')
  }

  /**
   * 獲取文檔預覽 URL
   */
  async getPreviewUrl(documentId: string): Promise<{ preview_url: string }> {
    return apiClient.get<{ preview_url: string }>(`/documents/${documentId}/preview`)
  }

  /**
   * 獲取文檔縮圖 URL
   */
  async getThumbnailUrl(documentId: string): Promise<{ thumbnail_url: string }> {
    return apiClient.get<{ thumbnail_url: string }>(`/documents/${documentId}/thumbnail`)
  }
}

// 創建默認實例
export const documentsApi = new DocumentsApi()

// 便捷方法
export const documents = {
  upload: (request: DocumentUploadRequest) => documentsApi.uploadDocument(request),
  uploadBatch: (files: File[], companyId: number, options?: any) =>
    documentsApi.uploadDocuments(files, companyId, options),
  getStatus: (documentId: string) => documentsApi.getDocumentStatus(documentId),
  getList: (params: DocumentListParams) => documentsApi.getDocuments(params),
  get: (documentId: string) => documentsApi.getDocument(documentId),
  update: (documentId: string, updates: any) => documentsApi.updateDocument(documentId, updates),
  delete: (documentId: string) => documentsApi.deleteDocument(documentId),
  batch: (request: BatchOperationRequest) => documentsApi.batchOperation(request),
  reprocess: (documentId: string) => documentsApi.reprocessDocument(documentId),
  stats: (companyId: number) => documentsApi.getDocumentStats(companyId),
  search: (query: string, companyId: number, options?: any) =>
    documentsApi.searchDocuments(query, companyId, options),
  categories: {
    list: (companyId: number) => documentsApi.getCategories(companyId),
    create: (companyId: number, category: any) => documentsApi.createCategory(companyId, category),
    update: (categoryId: string, updates: any) => documentsApi.updateCategory(categoryId, updates),
    delete: (categoryId: string) => documentsApi.deleteCategory(categoryId),
  },
  tags: {
    list: (companyId: number) => documentsApi.getTags(companyId),
    create: (companyId: number, tag: any) => documentsApi.createTag(companyId, tag),
    delete: (tagId: string) => documentsApi.deleteTag(tagId),
  },
  export: (companyId: number, options: DocumentExportOptions) =>
    documentsApi.exportDocuments(companyId, options),
  download: (documentId: string) => documentsApi.downloadDocument(documentId),
  config: () => documentsApi.getUploadConfig(),
}
