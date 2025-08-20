"use client"

import React, { useState, useCallback } from "react"
import { Upload, File, X } from "lucide-react"
import { documentsApi } from "@/lib/api"

interface DocumentUploadProps {
  companyId: number
  onUploadComplete?: (result: unknown) => void
  onUploadError?: (error: string) => void
  className?: string
}

export function DocumentUpload({
  companyId,
  onUploadComplete,
  onUploadError,
  className,
}: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  // 處理檔案拖拽
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    setSelectedFiles(files)
  }, [])

  // 處理檔案選擇
  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || [])
      setSelectedFiles(files)
    },
    []
  )

  // 移除選中的檔案
  const removeFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  // 上傳檔案
  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)
    setUploadProgress(0)

    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i]
        const formData = new FormData()
        formData.append("file", file)
        formData.append("company_id", companyId.toString())

        const result = await documentsApi.upload(formData)

        setUploadProgress(((i + 1) / selectedFiles.length) * 100)

        if (onUploadComplete) {
          onUploadComplete(result)
        }
      }

      // 清除選中的檔案
      setSelectedFiles([])
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "上傳失敗"
      if (onUploadError) {
        onUploadError(errorMessage)
      }
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [selectedFiles, companyId, onUploadComplete, onUploadError])

  return (
    <div className={className}>
      {/* 拖拽上傳區域 */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${
            isDragging
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-gray-400"
          }
        `}>
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">上傳文檔</h3>
        <p className="text-sm text-gray-500 mb-4">
          拖拽檔案到此處，或點擊選擇檔案
        </p>
        <input
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
          accept=".pdf,.doc,.docx,.txt,.md"
        />
        <label
          htmlFor="file-upload"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer">
          選擇檔案
        </label>
        <p className="text-xs text-gray-400 mt-2">
          支援 PDF, DOC, DOCX, TXT, MD 格式，單檔最大 50MB
        </p>
      </div>

      {/* 選中的檔案列表 */}
      {selectedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-gray-900">選中的檔案：</h4>
          {selectedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <File className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={() => removeFile(index)}
                className="text-gray-400 hover:text-red-500">
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}

          {/* 上傳按鈕 */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              onClick={() => setSelectedFiles([])}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
              清除
            </button>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50">
              {uploading
                ? `上傳中... ${uploadProgress.toFixed(0)}%`
                : "開始上傳"}
            </button>
          </div>
        </div>
      )}

      {/* 上傳進度 */}
      {uploading && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>上傳進度</span>
            <span>{uploadProgress.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
