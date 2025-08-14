/**
 * 文檔管理相關 hooks
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { documents } from '@/lib/api/documents'
import type {
  DocumentMetadata,
  DocumentListParams,
  DocumentListResponse,
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentStatusResponse,
  UploadProgress,
  BatchOperationRequest,
  DocumentStats,
} from '@/types/document'

/**
 * 文檔列表管理 hook
 */
export function useDocuments(params: DocumentListParams) {
  const [data, setData] = useState<DocumentListResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await documents.getList(params)
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取文檔列表失敗')
    } finally {
      setLoading(false)
    }
  }, [params])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  const refresh = useCallback(() => {
    fetchDocuments()
  }, [fetchDocuments])

  return {
    documents: data?.documents || [],
    total: data?.total || 0,
    page: data?.page || 1,
    limit: data?.limit || 20,
    hasNext: data?.has_next || false,
    hasPrev: data?.has_prev || false,
    loading,
    error,
    refresh,
  }
}

/**
 * 文檔上傳管理 hook
 */
export function useDocumentUpload() {
  const [uploads, setUploads] = useState<Map<string, UploadProgress>>(new Map())
  const [isUploading, setIsUploading] = useState(false)
  const abortControllersRef = useRef<Map<string, AbortController>>(new Map())

  const uploadDocument = useCallback(async (request: DocumentUploadRequest) => {
    const fileId = `${request.file.name}-${Date.now()}`
    const abortController = new AbortController()
    abortControllersRef.current.set(fileId, abortController)

    // 初始化上傳進度
    const initialProgress: UploadProgress = {
      file_id: fileId,
      filename: request.file.name,
      progress: 0,
      status: 'uploading',
      uploaded_bytes: 0,
      total_bytes: request.file.size,
    }

    setUploads(prev => new Map(prev.set(fileId, initialProgress)))
    setIsUploading(true)

    try {
      // 模擬上傳進度（實際應該從 API 回應中獲取）
      const progressInterval = setInterval(() => {
        setUploads(prev => {
          const current = prev.get(fileId)
          if (!current || current.status !== 'uploading') {
            clearInterval(progressInterval)
            return prev
          }

          const newProgress = Math.min(current.progress + Math.random() * 10, 90)
          const newUploaded = Math.floor((newProgress / 100) * current.total_bytes)
          
          return new Map(prev.set(fileId, {
            ...current,
            progress: newProgress,
            uploaded_bytes: newUploaded,
          }))
        })
      }, 500)

      const response = await documents.upload(request)

      clearInterval(progressInterval)

      // 更新為處理中狀態
      setUploads(prev => new Map(prev.set(fileId, {
        ...initialProgress,
        progress: 100,
        status: 'processing',
        uploaded_bytes: request.file.size,
      })))

      // 輪詢處理狀態
      const pollStatus = async () => {
        try {
          const status = await documents.getStatus(response.task_id)
          
          setUploads(prev => {
            const current = prev.get(fileId)
            if (!current) return prev

            return new Map(prev.set(fileId, {
              ...current,
              status: status.status === 'completed' ? 'completed' : 
                     status.status === 'failed' ? 'error' : 'processing',
              progress: status.progress,
              error: status.error,
            }))
          })

          if (status.status === 'completed' || status.status === 'failed') {
            return
          }

          // 繼續輪詢
          setTimeout(pollStatus, 2000)
        } catch (err) {
          setUploads(prev => {
            const current = prev.get(fileId)
            if (!current) return prev

            return new Map(prev.set(fileId, {
              ...current,
              status: 'error',
              error: err instanceof Error ? err.message : '狀態查詢失敗',
            }))
          })
        }
      }

      pollStatus()

      return response
    } catch (err) {
      setUploads(prev => new Map(prev.set(fileId, {
        ...initialProgress,
        status: 'error',
        error: err instanceof Error ? err.message : '上傳失敗',
      })))
      throw err
    } finally {
      abortControllersRef.current.delete(fileId)
      
      // 檢查是否還有其他上傳中的檔案
      setUploads(prev => {
        const hasUploading = Array.from(prev.values()).some(
          upload => upload.status === 'uploading' || upload.status === 'processing'
        )
        setIsUploading(hasUploading)
        return prev
      })
    }
  }, [])

  const uploadMultiple = useCallback(async (
    files: File[], 
    companyId: number, 
    options?: {
      category?: string
      description?: string
      tags?: string[]
    }
  ) => {
    const uploadPromises = files.map(file => 
      uploadDocument({
        file,
        company_id: companyId,
        ...options,
      })
    )

    return Promise.allSettled(uploadPromises)
  }, [uploadDocument])

  const cancelUpload = useCallback((fileId: string) => {
    const controller = abortControllersRef.current.get(fileId)
    if (controller) {
      controller.abort()
      abortControllersRef.current.delete(fileId)
    }

    setUploads(prev => {
      const newMap = new Map(prev)
      newMap.delete(fileId)
      return newMap
    })
  }, [])

  const clearCompleted = useCallback(() => {
    setUploads(prev => {
      const newMap = new Map()
      prev.forEach((upload, fileId) => {
        if (upload.status === 'uploading' || upload.status === 'processing') {
          newMap.set(fileId, upload)
        }
      })
      return newMap
    })
  }, [])

  const clearAll = useCallback(() => {
    // 取消所有進行中的上傳
    abortControllersRef.current.forEach(controller => controller.abort())
    abortControllersRef.current.clear()
    
    setUploads(new Map())
    setIsUploading(false)
  }, [])

  return {
    uploads: Array.from(uploads.values()),
    isUploading,
    uploadDocument,
    uploadMultiple,
    cancelUpload,
    clearCompleted,
    clearAll,
  }
}

/**
 * 文檔狀態管理 hook
 */
export function useDocumentStatus(documentId: string | null) {
  const [status, setStatus] = useState<DocumentStatusResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!documentId) return

    setLoading(true)
    setError(null)

    try {
      const response = await documents.getStatus(documentId)
      setStatus(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取狀態失敗')
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  return {
    status,
    loading,
    error,
    refresh: fetchStatus,
  }
}

/**
 * 批次操作 hook
 */
export function useBatchOperations() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const executeBatch = useCallback(async (request: BatchOperationRequest) => {
    setLoading(true)
    setError(null)

    try {
      const response = await documents.batch(request)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '批次操作失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    executeBatch,
    loading,
    error,
  }
}

/**
 * 文檔統計 hook
 */
export function useDocumentStats(companyId: number) {
  const [stats, setStats] = useState<DocumentStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await documents.stats(companyId)
      setStats(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取統計資訊失敗')
    } finally {
      setLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return {
    stats,
    loading,
    error,
    refresh: fetchStats,
  }
}
