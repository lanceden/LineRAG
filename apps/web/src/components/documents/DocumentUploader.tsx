'use client'

import React, { useCallback, useState, useRef } from 'react'
import { Upload, X, FileText, AlertCircle, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useDocumentUpload } from '@/hooks/useDocuments'
import type { SupportedFileType } from '@/types/document'

interface DocumentUploaderProps {
  companyId: number
  onUploadSuccess?: (documentId: string) => void
  onUploadError?: (error: string) => void
  maxFileSize?: number // bytes
  maxFiles?: number
  allowedTypes?: SupportedFileType[]
  category?: string
  description?: string
  tags?: string[]
  className?: string
}

const DEFAULT_ALLOWED_TYPES: SupportedFileType[] = [
  '.pdf', '.docx', '.pptx', '.xlsx', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.txt'
]

const DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

export function DocumentUploader({
  companyId,
  onUploadSuccess,
  onUploadError,
  maxFileSize = DEFAULT_MAX_FILE_SIZE,
  maxFiles = 10,
  allowedTypes = DEFAULT_ALLOWED_TYPES,
  category,
  description,
  tags,
  className,
}: DocumentUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const { uploads, isUploading, uploadMultiple, cancelUpload, clearCompleted } = useDocumentUpload()

  // 檔案驗證
  const validateFile = useCallback((file: File): string | null => {
    // 檢查檔案大小
    if (file.size > maxFileSize) {
      return `檔案 "${file.name}" 超過大小限制 (${Math.round(maxFileSize / 1024 / 1024)}MB)`
    }

    // 檢查檔案類型
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!allowedTypes.includes(fileExtension as SupportedFileType)) {
      return `檔案 "${file.name}" 格式不支援。支援格式：${allowedTypes.join(', ')}`
    }

    return null
  }, [maxFileSize, allowedTypes])

  // 處理檔案選擇
  const handleFileSelect = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files)
    const errors: string[] = []
    const validFiles: File[] = []

    // 檢查檔案數量限制
    if (selectedFiles.length + fileArray.length > maxFiles) {
      errors.push(`最多只能選擇 ${maxFiles} 個檔案`)
      return
    }

    // 驗證每個檔案
    fileArray.forEach(file => {
      const error = validateFile(file)
      if (error) {
        errors.push(error)
      } else {
        validFiles.push(file)
      }
    })

    if (errors.length > 0) {
      onUploadError?.(errors.join('\n'))
      return
    }

    setSelectedFiles(prev => [...prev, ...validFiles])
  }, [selectedFiles.length, maxFiles, validateFile, onUploadError])

  // 拖拽處理
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files)
    }
  }, [handleFileSelect])

  // 檔案輸入處理
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files)
    }
    // 清空 input 值，允許重複選擇相同檔案
    e.target.value = ''
  }, [handleFileSelect])

  // 移除選中的檔案
  const removeFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  // 開始上傳
  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0) return

    try {
      const results = await uploadMultiple(selectedFiles, companyId, {
        category,
        description,
        tags,
      })

      // 處理上傳結果
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          onUploadSuccess?.(result.value.task_id)
        } else {
          onUploadError?.(`檔案 "${selectedFiles[index].name}" 上傳失敗：${result.reason}`)
        }
      })

      // 清空選中的檔案
      setSelectedFiles([])
    } catch (error) {
      onUploadError?.(error instanceof Error ? error.message : '上傳失敗')
    }
  }, [selectedFiles, companyId, category, description, tags, uploadMultiple, onUploadSuccess, onUploadError])

  // 點擊選擇檔案
  const handleSelectFiles = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  // 格式化檔案大小
  const formatFileSize = useCallback((bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }, [])

  return (
    <div className={cn('space-y-4', className)}>
      {/* 拖拽上傳區域 */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400',
          isUploading && 'opacity-50 pointer-events-none'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <div className="space-y-2">
          <p className="text-lg font-medium text-gray-900">
            拖拽檔案到此處或
            <button
              type="button"
              onClick={handleSelectFiles}
              className="text-blue-600 hover:text-blue-500 ml-1"
              disabled={isUploading}
            >
              點擊選擇
            </button>
          </p>
          <p className="text-sm text-gray-500">
            支援格式：{allowedTypes.join(', ')}
          </p>
          <p className="text-sm text-gray-500">
            最大檔案大小：{Math.round(maxFileSize / 1024 / 1024)}MB，最多 {maxFiles} 個檔案
          </p>
        </div>
      </div>

      {/* 隱藏的檔案輸入 */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={allowedTypes.join(',')}
        onChange={handleFileInputChange}
        className="hidden"
        disabled={isUploading}
      />

      {/* 選中的檔案列表 */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">選中的檔案 ({selectedFiles.length})</h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {selectedFiles.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="text-gray-400 hover:text-red-500"
                  disabled={isUploading}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
          
          {/* 上傳按鈕 */}
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setSelectedFiles([])}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={isUploading}
            >
              清空
            </button>
            <button
              type="button"
              onClick={handleUpload}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
              disabled={isUploading || selectedFiles.length === 0}
            >
              {isUploading ? '上傳中...' : `上傳 ${selectedFiles.length} 個檔案`}
            </button>
          </div>
        </div>
      )}

      {/* 上傳進度列表 */}
      {uploads.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-gray-900">上傳進度</h4>
            <button
              type="button"
              onClick={clearCompleted}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              清除已完成
            </button>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {uploads.map((upload) => (
              <div key={upload.file_id} className="p-3 bg-white border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {upload.status === 'completed' && (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    )}
                    {upload.status === 'error' && (
                      <AlertCircle className="h-4 w-4 text-red-500" />
                    )}
                    {(upload.status === 'uploading' || upload.status === 'processing') && (
                      <div className="h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    )}
                    <span className="text-sm font-medium text-gray-900">
                      {upload.filename}
                    </span>
                  </div>
                  {(upload.status === 'uploading' || upload.status === 'processing') && (
                    <button
                      type="button"
                      onClick={() => cancelUpload(upload.file_id)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
                
                {/* 進度條 */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                  <div
                    className={cn(
                      'h-2 rounded-full transition-all duration-300',
                      upload.status === 'completed' ? 'bg-green-500' :
                      upload.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                    )}
                    style={{ width: `${upload.progress}%` }}
                  />
                </div>
                
                <div className="flex justify-between text-xs text-gray-500">
                  <span>
                    {upload.status === 'uploading' && '上傳中'}
                    {upload.status === 'processing' && '處理中'}
                    {upload.status === 'completed' && '完成'}
                    {upload.status === 'error' && '失敗'}
                  </span>
                  <span>{Math.round(upload.progress)}%</span>
                </div>
                
                {upload.error && (
                  <p className="text-xs text-red-500 mt-1">{upload.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
