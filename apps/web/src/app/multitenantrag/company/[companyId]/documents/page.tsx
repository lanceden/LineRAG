"use client"

import React, { useState, useCallback } from "react"
import { useParams } from "next/navigation"
import {
  Upload,
  Plus,
  Settings,
  BarChart3,
  Search,
  Filter,
  Download,
  Trash2,
  RefreshCw,
} from "lucide-react"
import { DocumentUploader } from "@/components/documents/DocumentUploader"
import { DocumentList } from "@/components/documents/DocumentList"
import {
  DocumentUploadGuard,
  DocumentDeleteGuard,
  DocumentBatchGuard,
  DocumentAnalyticsGuard,
  useDocumentPermissions,
} from "@/components/documents/DocumentPermissionGuard"
import { CompanyPageTitle } from "@/components/CompanySelector"
import {
  useDocuments,
  useDocumentStats,
  useBatchOperations,
} from "@/hooks/useDocuments"
import { documents } from "@/lib/api/documents"
import type { DocumentMetadata, DocumentListParams } from "@/types/document"

export default function DocumentsPage() {
  const params = useParams()
  const companyId = parseInt(params.companyId as string)

  // 權限檢查
  const permissions = useDocumentPermissions(companyId.toString())

  // 狀態管理
  const [showUploader, setShowUploader] = useState(false)
  const [viewMode, setViewMode] = useState<"grid" | "list">("list")
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [categoryFilter, setCategoryFilter] = useState<string>("all")

  // API hooks
  const documentParams: DocumentListParams = {
    company_id: companyId,
    page: currentPage,
    limit: 20,
    search: searchQuery || undefined,
    status: statusFilter !== "all" ? (statusFilter as unknown) : undefined,
    category: categoryFilter !== "all" ? categoryFilter : undefined,
    sort_by: "created_at",
    sort_order: "desc",
  }

  const {
    documents: documentList,
    total,
    loading: documentsLoading,
    error: documentsError,
    refresh: refreshDocuments,
  } = useDocuments(documentParams)

  const {
    stats,
    loading: statsLoading,
    refresh: refreshStats,
  } = useDocumentStats(companyId)

  const { executeBatch, loading: batchLoading } = useBatchOperations()

  // 處理文檔上傳成功
  const handleUploadSuccess = useCallback(
    (documentId: string) => {
      console.log("文檔上傳成功:", documentId)
      refreshDocuments()
      refreshStats()
    },
    [refreshDocuments, refreshStats]
  )

  // 處理文檔上傳錯誤
  const handleUploadError = useCallback((error: string) => {
    console.error("文檔上傳失敗:", error)
    // 這裡可以顯示錯誤通知
  }, [])

  // 處理文檔選擇
  const handleDocumentSelect = useCallback((documentId: string) => {
    setSelectedDocuments((prev) =>
      prev.includes(documentId)
        ? prev.filter((id) => id !== documentId)
        : [...prev, documentId]
    )
  }, [])

  // 處理全選
  const handleDocumentSelectAll = useCallback(
    (selected: boolean) => {
      setSelectedDocuments(selected ? documentList.map((doc) => doc.id) : [])
    },
    [documentList]
  )

  // 處理文檔檢視
  const handleDocumentView = useCallback((document: DocumentMetadata) => {
    console.log("檢視文檔:", document)
    // 這裡可以開啟文檔預覽模態框
  }, [])

  // 處理文檔編輯
  const handleDocumentEdit = useCallback((document: DocumentMetadata) => {
    console.log("編輯文檔:", document)
    // 這裡可以開啟文檔編輯模態框
  }, [])

  // 處理文檔下載
  const handleDocumentDownload = useCallback(
    async (document: DocumentMetadata) => {
      try {
        const blob = await documents.download(document.id)
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = document.filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } catch (error) {
        console.error("下載失敗:", error)
      }
    },
    []
  )

  // 處理文檔刪除
  const handleDocumentDelete = useCallback(
    async (document: DocumentMetadata) => {
      if (!confirm(`確定要刪除文檔 "${document.filename}" 嗎？`)) {
        return
      }

      try {
        await documents.delete(document.id)
        refreshDocuments()
        refreshStats()
      } catch (error) {
        console.error("刪除失敗:", error)
      }
    },
    [refreshDocuments, refreshStats]
  )

  // 處理批次刪除
  const handleBatchDelete = useCallback(async () => {
    if (selectedDocuments.length === 0) return

    if (!confirm(`確定要刪除選中的 ${selectedDocuments.length} 個文檔嗎？`)) {
      return
    }

    try {
      await executeBatch({
        document_ids: selectedDocuments,
        action: "delete",
      })
      setSelectedDocuments([])
      refreshDocuments()
      refreshStats()
    } catch (error) {
      console.error("批次刪除失敗:", error)
    }
  }, [selectedDocuments, executeBatch, refreshDocuments, refreshStats])

  // 處理批次下載
  const handleBatchDownload = useCallback(async () => {
    if (selectedDocuments.length === 0) return

    try {
      // 這裡可以實作批次下載邏輯
      console.log("批次下載:", selectedDocuments)
    } catch (error) {
      console.error("批次下載失敗:", error)
    }
  }, [selectedDocuments])

  return (
    <div className="space-y-6">
      {/* 頁面標題和操作 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CompanyPageTitle title="知識庫管理" />
          <p className="mt-1 text-sm text-gray-500">
            管理公司的文檔和知識庫內容
          </p>
        </div>

        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <button
            onClick={() => refreshDocuments()}
            disabled={documentsLoading}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            <RefreshCw
              className={`h-4 w-4 mr-2 ${
                documentsLoading ? "animate-spin" : ""
              }`}
            />
            重新整理
          </button>

          <DocumentUploadGuard companyId={companyId.toString()}>
            <button
              onClick={() => setShowUploader(!showUploader)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              <Upload className="h-4 w-4 mr-2" />
              上傳文檔
            </button>
          </DocumentUploadGuard>
        </div>
      </div>

      {/* 統計資訊 */}
      <DocumentAnalyticsGuard companyId={companyId.toString()}>
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BarChart3 className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        總文檔數
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.total_documents}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Settings className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        處理中
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.processing_queue}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Plus className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        最近上傳
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.recent_uploads}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Download className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        總大小
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {Math.round(stats.total_size / 1024 / 1024)} MB
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </DocumentAnalyticsGuard>

      {/* 文檔上傳器 */}
      {showUploader && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">上傳文檔</h2>
            <button
              onClick={() => setShowUploader(false)}
              className="text-gray-400 hover:text-gray-600">
              ×
            </button>
          </div>

          <DocumentUploader
            companyId={companyId}
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </div>
      )}

      {/* 批次操作列 */}
      <DocumentBatchGuard companyId={companyId.toString()}>
        {selectedDocuments.length > 0 && (
          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">
                已選擇 {selectedDocuments.length} 個文檔
              </span>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleBatchDownload}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                  <Download className="h-4 w-4 mr-2" />
                  批次下載
                </button>
                <DocumentDeleteGuard companyId={companyId.toString()}>
                  <button
                    onClick={handleBatchDelete}
                    disabled={batchLoading}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50">
                    <Trash2 className="h-4 w-4 mr-2" />
                    批次刪除
                  </button>
                </DocumentDeleteGuard>
              </div>
            </div>
          </div>
        )}
      </DocumentBatchGuard>

      {/* 文檔列表 */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">文檔列表</h2>
        </div>

        <div className="p-6">
          <DocumentList
            documents={documentList}
            loading={documentsLoading}
            viewMode={viewMode}
            selectedDocuments={selectedDocuments}
            onDocumentSelect={handleDocumentSelect}
            onDocumentSelectAll={handleDocumentSelectAll}
            onDocumentView={handleDocumentView}
            onDocumentEdit={handleDocumentEdit}
            onDocumentDownload={handleDocumentDownload}
            onDocumentDelete={handleDocumentDelete}
            onViewModeChange={setViewMode}
          />
        </div>
      </div>

      {/* 分頁 */}
      {total > 20 && (
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 rounded-lg shadow">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50">
              上一頁
            </button>
            <button
              onClick={() => setCurrentPage((prev) => prev + 1)}
              disabled={currentPage * 20 >= total}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50">
              下一頁
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                顯示第{" "}
                <span className="font-medium">
                  {(currentPage - 1) * 20 + 1}
                </span>{" "}
                到{" "}
                <span className="font-medium">
                  {Math.min(currentPage * 20, total)}
                </span>{" "}
                項， 共 <span className="font-medium">{total}</span> 項結果
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(1, prev - 1))
                  }
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50">
                  上一頁
                </button>
                <button
                  onClick={() => setCurrentPage((prev) => prev + 1)}
                  disabled={currentPage * 20 >= total}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50">
                  下一頁
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
