"use client"

import React, { useState, useEffect, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Upload,
  FileText,
  Trash2,
  Search,
  X,
  File,
  AlertCircle,
  CheckCircle,
  Clock,
  Loader2,
  Info,
} from "lucide-react"
import { Company } from "@/types/company"
import { DocumentMetadata } from "@/types/document"
import { documentsApi } from "@/lib/api"

interface DocumentManagementDialogProps {
  company: Company | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DocumentManagementDialog({
  company,
  open,
  onOpenChange,
}: DocumentManagementDialogProps) {
  const [activeTab, setActiveTab] = useState<"upload" | "list">("upload")
  const [documents, setDocuments] = useState<DocumentMetadata[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")

  // 文檔上傳相關狀態
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  // Toast 通知狀態
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState("")
  const [toastType, setToastType] = useState<"success" | "error" | "warning">(
    "success"
  )

  // 顯示 Toast 通知
  const showToastNotification = useCallback(
    (message: string, type: "success" | "error" | "warning" = "success") => {
      setToastMessage(message)
      setToastType(type)
      setShowToast(true)
      setTimeout(() => setShowToast(false), 5000) // 5秒後自動隱藏
    },
    []
  )

  // 載入文檔列表
  const loadDocuments = useCallback(async () => {
    if (!company) return

    setLoading(true)
    try {
      const result = await documentsApi.getCompanyDocuments(company.id)
      setDocuments(result.documents || [])
    } catch (error) {
      console.error("載入文檔列表失敗:", error)
      showToastNotification("載入文檔列表失敗，請稍後重試", "error")
    } finally {
      setLoading(false)
    }
  }, [company, showToastNotification])

  useEffect(() => {
    if (open && activeTab === "list") {
      loadDocuments()
    }
  }, [open, activeTab, loadDocuments])

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
    if (selectedFiles.length === 0) {
      showToastNotification("請先選擇要上傳的檔案", "warning")
      return
    }
    if (!company) return

    setUploading(true)
    setUploadProgress(0)

    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i]
        const formData = new FormData()
        formData.append("file", file)
        formData.append("company_id", company.id.toString())

        await documentsApi.upload(formData)
        setUploadProgress(((i + 1) / selectedFiles.length) * 100)
      }

      setSelectedFiles([])
      // 顯示成功提示並切換到列表頁面
      showToastNotification(
        "文檔已成功上傳！AI 正在後台進行智能分析，通常需要 5-30 分鐘。您可以繼續其他操作，稍後回來查看分析結果。",
        "success"
      )
      setActiveTab("list")
      await loadDocuments()
    } catch (error) {
      console.error("上傳失敗:", error)
      showToastNotification("上傳失敗，請稍後重試", "error")
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [selectedFiles, company, loadDocuments, showToastNotification])

  // 刪除文檔
  const handleDeleteDocument = async (document: DocumentMetadata) => {
    try {
      await documentsApi.delete(document.id)
      showToastNotification(`文檔 "${document.filename}" 已成功刪除`, "success")
      await loadDocuments()
    } catch (error) {
      console.error("刪除文檔失敗:", error)
      showToastNotification("刪除文檔失敗，請稍後重試", "error")
    }
  }

  // 過濾文檔
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.filename
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || doc.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "processing":
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      case "queued":
        return <Clock className="h-4 w-4 text-yellow-600" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case "cancelled":
        return <X className="h-4 w-4 text-gray-600" />
      default:
        return <FileText className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800"
      case "processing":
        return "bg-blue-100 text-blue-800"
      case "queued":
        return "bg-yellow-100 text-yellow-800"
      case "failed":
        return "bg-red-100 text-red-800"
      case "cancelled":
        return "bg-gray-100 text-gray-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  if (!company) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>{company.name} - 文檔管理</span>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 flex flex-col overflow-auto">
          {/* 標籤導航 */}
          <div className="flex space-x-4 mb-6 border-b">
            <button
              onClick={() => setActiveTab("upload")}
              className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "upload"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}>
              <Upload className="h-4 w-4 inline mr-1" />
              上傳文檔
            </button>
            <button
              onClick={() => setActiveTab("list")}
              className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "list"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}>
              <FileText className="h-4 w-4 inline mr-1" />
              文檔列表 ({documents.length})
            </button>
          </div>

          {/* 標籤內容 */}
          <div className="flex-1 overflow-auto">
            {activeTab === "upload" && (
              <div className="h-full flex flex-col">
                {/* 緊湊的上傳區域 */}
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`
                    border-2 border-dashed rounded-lg p-3 text-center transition-colors mb-4
                    ${
                      isDragging
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-300 hover:border-gray-400"
                    }
                  `}>
                  <Upload className="mx-auto h-5 w-5 text-gray-400 mb-1" />
                  <p className="text-xs text-gray-500 mb-2">
                    拖拽檔案到此處或點擊選擇
                  </p>
                  <input
                    type="file"
                    multiple
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                    accept=".pdf,.doc,.docx,.txt,.md,.xlsx,.pptx,.jpg,.jpeg,.png,.bmp,.tiff"
                  />
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 cursor-pointer">
                    選擇檔案
                  </label>
                </div>

                {/* 檔案列表 - 緊湊型 */}
                {selectedFiles.length > 0 && (
                  <div className="flex-1 min-h-0">
                    <div className="text-xs font-medium text-gray-700 mb-2">
                      已選擇 {selectedFiles.length} 個檔案
                    </div>
                    <div className="h-32 overflow-y-auto border rounded p-2 space-y-1">
                      {selectedFiles.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-1.5 bg-gray-50 rounded text-xs">
                          <div className="flex items-center space-x-2 flex-1 min-w-0">
                            <File className="h-3 w-3 text-gray-400 flex-shrink-0" />
                            <div className="min-w-0 flex-1">
                              <p className="font-medium text-gray-900 truncate">
                                {file.name}
                              </p>
                              <p className="text-gray-500">
                                {(file.size / 1024 / 1024).toFixed(1)} MB
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={() => removeFile(index)}
                            className="text-gray-400 hover:text-red-500 p-0.5">
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 固定在底部的按鈕區域 */}
                <div className="mt-4 pt-3 border-t">
                  <div className="flex justify-between items-center">
                    <div className="text-xs text-gray-500">
                      支援 PDF, DOC, DOCX, TXT, MD
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedFiles([])}
                        disabled={selectedFiles.length === 0}>
                        清除
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleUpload}
                        disabled={uploading || selectedFiles.length === 0}>
                        {uploading ? (
                          <>
                            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                            {uploadProgress.toFixed(0)}%
                          </>
                        ) : (
                          "開始上傳"
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* 上傳進度條 */}
                  {uploading && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === "list" && (
              <div className="flex flex-col h-full space-y-4">
                {/* 搜尋和過濾 */}
                <div className="flex space-x-3">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="搜尋文檔名稱..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="all">所有狀態</option>
                    <option value="completed">已完成</option>
                    <option value="processing">處理中</option>
                    <option value="queued">排隊中</option>
                    <option value="failed">失敗</option>
                    <option value="cancelled">已取消</option>
                  </select>
                </div>

                {/* 文檔列表 */}
                <div className="flex-1 overflow-auto">
                  {loading ? (
                    <div className="flex items-center justify-center h-32">
                      <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                      <span className="ml-2 text-gray-500">載入中...</span>
                    </div>
                  ) : filteredDocuments.length === 0 ? (
                    <div className="text-center py-12">
                      <FileText className="mx-auto h-12 w-12 text-gray-300 mb-4" />
                      <p className="text-gray-500">
                        {documents.length === 0
                          ? "尚未上傳任何文檔"
                          : "沒有符合條件的文檔"}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredDocuments.map((doc) => (
                        <div
                          key={doc.id}
                          className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                          <div className="flex items-center space-x-3 flex-1">
                            {getStatusIcon(doc.status)}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {doc.filename}
                              </p>
                              <div className="flex items-center space-x-4 text-xs text-gray-500">
                                <span>
                                  {(doc.file_size / 1024 / 1024).toFixed(2)} MB
                                </span>
                                <span>{doc.file_type.toUpperCase()}</span>
                                <span>
                                  {new Date(doc.created_at).toLocaleDateString(
                                    "zh-TW"
                                  )}
                                </span>
                              </div>
                              {doc.error_message && (
                                <p className="text-xs text-red-600 mt-1">
                                  {doc.error_message}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Badge className={getStatusColor(doc.status)}>
                              {doc.status === "completed" && "已完成"}
                              {doc.status === "processing" && "處理中"}
                              {doc.status === "queued" && "排隊中"}
                              {doc.status === "failed" && "失敗"}
                              {doc.status === "cancelled" && "已取消"}
                            </Badge>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteDocument(doc)}>
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            關閉
          </Button>
        </div>
      </DialogContent>

      {/* Toast 通知組件 */}
      {showToast && (
        <div
          className={`fixed top-4 right-4 p-4 rounded-lg shadow-lg z-[9999] transform transition-all duration-300 ${
            toastType === "success"
              ? "bg-green-500 text-white"
              : toastType === "error"
              ? "bg-red-500 text-white"
              : "bg-yellow-500 text-white"
          }`}>
          <div className="flex items-center space-x-2">
            {toastType === "success" && <CheckCircle className="h-4 w-4" />}
            {toastType === "error" && <AlertCircle className="h-4 w-4" />}
            {toastType === "warning" && <Info className="h-4 w-4" />}
            <span>{toastMessage}</span>
            <button
              onClick={() => setShowToast(false)}
              className="ml-2 hover:bg-white hover:bg-opacity-20 rounded p-1">
              <X className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}
    </Dialog>
  )
}
