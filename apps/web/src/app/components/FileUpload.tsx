"use client"

import { useState, useRef, useEffect, useCallback } from "react"

interface UploadedFile {
  name: string
  size: number
  type: string
  lastModified: number
}

interface DocumentFromAPI {
  doc_id: string
  filename: string
  upload_date: string
  chunk_count: number
  processing_method?: string
}

interface FileUploadProps {
  onUploadSuccess?: (fileName: string) => void
  onUploadError?: (error: string) => void
}

export default function FileUpload({
  onUploadSuccess,
  onUploadError,
}: FileUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [documentsFromAPI, setDocumentsFromAPI] = useState<DocumentFromAPI[]>(
    []
  )
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [isDeletingDoc, setIsDeletingDoc] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [useOCR, setUseOCR] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 支援的檔案類型
  const acceptedTypes = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
      ".docx",
  }

  const acceptedExtensions = Object.values(acceptedTypes).join(",")

  // 獲取已上傳的文檔列表
  const fetchDocuments = useCallback(async () => {
    setIsLoadingDocuments(true)
    try {
      // 使用 Next.js API 路由來避免 CORS 問題
      const response = await fetch("/api/upload")

      if (!response.ok) {
        const errorText = await response.text()
        console.error("API response error:", response.status, errorText)
        throw new Error(`無法獲取文檔列表: ${response.status}`)
      }

      const data = await response.json()
      console.log("Documents fetched successfully:", data)
      setDocumentsFromAPI(data.documents || [])
    } catch (error) {
      console.error("獲取文檔列表失敗:", error)
      // Don't call onUploadError here to avoid UI errors during normal loading
      // onUploadError?.("無法載入文檔列表")
    } finally {
      setIsLoadingDocuments(false)
    }
  }, [])

  // 刪除文檔
  const deleteDocument = async (docId: string, filename: string) => {
    if (!confirm(`確定要刪除文檔「${filename}」嗎？此操作無法復原。`)) {
      return
    }

    setIsDeletingDoc(docId)
    try {
      // 使用 Next.js API 路由來刪除文檔
      const response = await fetch(`/api/upload?docId=${docId}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "刪除失敗")
      }

      // 重新獲取文檔列表
      await fetchDocuments()
      onUploadSuccess?.(`成功刪除文檔：${filename}`)
    } catch (error) {
      console.error("刪除文檔失敗:", error)
      onUploadError?.(error instanceof Error ? error.message : "刪除文檔失敗")
    } finally {
      setIsDeletingDoc(null)
    }
  }

  // 組件載入時獲取文檔列表
  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // 檢查檔案類型
  const isValidFileType = (file: File): boolean => {
    return (
      Object.keys(acceptedTypes).includes(file.type) ||
      Object.values(acceptedTypes).some((ext) =>
        file.name.toLowerCase().endsWith(ext)
      )
    )
  }

  // 格式化檔案大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  // 處理檔案上傳
  const handleFileUpload = async (files: FileList) => {
    const validFiles = Array.from(files).filter(isValidFileType)

    if (validFiles.length === 0) {
      onUploadError?.("請選擇 PDF 或 Word 檔案")
      return
    }

    if (validFiles.length !== files.length) {
      onUploadError?.("部分檔案格式不支援，僅支援 PDF 和 Word 檔案")
    }

    setIsUploading(true)

    try {
      for (const file of validFiles) {
        const formData = new FormData()
        formData.append("file", file)
        formData.append("use_ocr", useOCR.toString())

        const response = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `上傳 ${file.name} 失敗`)
        }

        // 更新已上傳檔案列表
        const uploadedFile: UploadedFile = {
          name: file.name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
        }

        setUploadedFiles((prev) => [...prev, uploadedFile])
        onUploadSuccess?.(file.name)

        // 重新獲取文檔列表以顯示新上傳的文檔
        await fetchDocuments()
      }
    } catch (error) {
      console.error("Upload error:", error)
      onUploadError?.(error instanceof Error ? error.message : "上傳失敗")
    } finally {
      setIsUploading(false)
    }
  }

  // 拖拽處理
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files)
    }
  }

  const triggerFileSelect = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">文檔上傳</h2>
        <p className="text-gray-600 text-sm mb-4">
          支援 PDF 和 Word 檔案 (.pdf, .doc, .docx)，上傳後將自動加入知識庫
        </p>

        {/* OCR 選項 */}
        <div className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <input
            type="checkbox"
            id="useOCR"
            checked={useOCR}
            onChange={(e) => setUseOCR(e.target.checked)}
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            disabled={isUploading}
          />
          <label htmlFor="useOCR" className="flex-1 cursor-pointer">
            <div className="font-medium text-gray-900">啟用 OCR 模式</div>
            <div className="text-sm text-gray-600">
              適用於掃描版 PDF 或圖片化文檔，使用 AI 視覺模型進行文字識別
            </div>
          </label>
          <div className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
            {useOCR ? "🤖 AI OCR" : "📄 傳統"}
          </div>
        </div>
      </div>

      {/* 上傳區域 */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
          ${
            dragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-gray-400"
          }
          ${isUploading ? "opacity-50 cursor-not-allowed" : ""}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={!isUploading ? triggerFileSelect : undefined}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedExtensions}
          onChange={handleFileSelect}
          className="hidden"
          disabled={isUploading}
        />

        <div className="space-y-4">
          <div className="mx-auto w-16 h-16 text-gray-400">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          {isUploading ? (
            <div>
              <p className="text-lg font-medium text-blue-600">
                {useOCR ? "🤖 AI OCR 處理中..." : "📄 上傳處理中..."}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {useOCR
                  ? "正在使用視覺模型識別文字，請稍候..."
                  : "正在處理文檔內容..."}
              </p>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full animate-pulse"
                  style={{ width: "60%" }}></div>
              </div>
            </div>
          ) : (
            <div>
              <p className="text-lg font-medium text-gray-700">
                拖拽檔案到此處或點擊選擇檔案
              </p>
              <p className="text-sm text-gray-500">
                支援 PDF、DOC、DOCX 格式 •{" "}
                {useOCR ? "🤖 AI OCR 模式" : "📄 傳統模式"}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 知識庫中的文檔列表 */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium">知識庫文檔</h3>
          <button
            onClick={fetchDocuments}
            disabled={isLoadingDocuments}
            className="px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 disabled:opacity-50">
            {isLoadingDocuments ? "載入中..." : "重新整理"}
          </button>
        </div>

        {isLoadingDocuments ? (
          <div className="text-center py-4">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-sm text-gray-500">載入文檔列表中...</p>
          </div>
        ) : documentsFromAPI.length > 0 ? (
          <div className="space-y-2">
            {documentsFromAPI.map((doc) => (
              <div
                key={doc.doc_id}
                className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 text-blue-600">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <p className="font-medium text-gray-900">
                        {doc.filename}
                      </p>
                      {doc.processing_method === "ocr" && (
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                          🤖 OCR
                        </span>
                      )}
                      {doc.processing_method === "traditional" && (
                        <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                          📄 傳統
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">
                      上傳時間: {doc.upload_date} • 分塊數: {doc.chunk_count}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => deleteDocument(doc.doc_id, doc.filename)}
                  disabled={isDeletingDoc === doc.doc_id}
                  className="px-3 py-1 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed">
                  {isDeletingDoc === doc.doc_id ? "刪除中..." : "刪除"}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <div className="w-16 h-16 mx-auto mb-3 text-gray-300">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <p>知識庫中還沒有文檔</p>
            <p className="text-sm">上傳 PDF 或 Word 文檔開始使用</p>
          </div>
        )}
      </div>

      {/* 本次上傳的檔案列表 */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-3">本次上傳檔案</h3>
          <div className="space-y-2">
            {uploadedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 text-green-600">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <span className="text-green-600 text-sm font-medium">
                  已上傳
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 使用說明 */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">使用說明：</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• 支援的檔案格式：PDF (.pdf)、Word (.doc, .docx)</li>
          <li>• 可同時上傳多個檔案</li>
          <li>
            • <strong>傳統模式</strong>：直接提取文檔中的文字內容（速度快）
          </li>
          <li>
            • <strong>OCR 模式</strong>：先轉圖片再用 AI
            視覺模型識別文字（適合掃描版文檔）
          </li>
          <li>• 上傳後檔案將自動處理並加入 AI 知識庫</li>
          <li>• 處理完成後即可在聊天中詢問相關內容</li>
        </ul>

        <div className="mt-3 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-sm text-blue-800">
            <strong>💡 建議：</strong>
            如果是掃描版 PDF 或圖片化文檔，請啟用 OCR
            模式以獲得更好的文字識別效果。 OCR 處理時間較長，請耐心等候。
          </p>
        </div>
      </div>
    </div>
  )
}
