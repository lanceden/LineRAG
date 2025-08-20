"use client"

import React, { useState, useCallback } from "react"
import {
  FileText,
  Search,
  Filter,
  MoreVertical,
  Download,
  Trash2,
  Edit,
  Eye,
  Grid,
  List,
  Calendar,
  User,
  Tag,
  FolderOpen,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { ProcessingStatusBadge } from "./ProcessingStatus"
import type { DocumentMetadata, DocumentStatus } from "@/types/document"

interface DocumentListProps {
  documents: DocumentMetadata[]
  loading?: boolean
  viewMode?: "grid" | "list"
  selectedDocuments?: string[]
  onDocumentSelect?: (documentId: string) => void
  onDocumentSelectAll?: (selected: boolean) => void
  onDocumentView?: (document: DocumentMetadata) => void
  onDocumentEdit?: (document: DocumentMetadata) => void
  onDocumentDownload?: (document: DocumentMetadata) => void
  onDocumentDelete?: (document: DocumentMetadata) => void
  onViewModeChange?: (mode: "grid" | "list") => void
  className?: string
}

// 檔案類型圖標映射
const fileTypeIcons = {
  ".pdf": "📄",
  ".docx": "📝",
  ".pptx": "📊",
  ".xlsx": "📈",
  ".jpg": "🖼️",
  ".jpeg": "🖼️",
  ".png": "🖼️",
  ".bmp": "🖼️",
  ".tiff": "🖼️",
  ".txt": "📄",
  default: "📄",
}

// 導出 DocumentGrid 組件作為別名
export const DocumentGrid = DocumentList

export function DocumentList({
  documents,
  loading = false,
  viewMode = "list",
  selectedDocuments = [],
  onDocumentSelect,
  onDocumentSelectAll,
  onDocumentView,
  onDocumentEdit,
  onDocumentDownload,
  onDocumentDelete,
  onViewModeChange,
  className,
}: DocumentListProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | "all">(
    "all"
  )
  const [categoryFilter, setCategoryFilter] = useState<string>("all")

  // 格式化檔案大小
  const formatFileSize = useCallback((bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }, [])

  // 格式化日期
  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }, [])

  // 過濾文檔
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      searchQuery === "" ||
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description?.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus = statusFilter === "all" || doc.status === statusFilter
    const matchesCategory =
      categoryFilter === "all" || doc.category === categoryFilter

    return matchesSearch && matchesStatus && matchesCategory
  })

  // 獲取所有分類
  const categories = Array.from(
    new Set(documents.map((doc) => doc.category).filter(Boolean))
  )

  // 處理全選
  const handleSelectAll = useCallback(
    (checked: boolean) => {
      onDocumentSelectAll?.(checked)
    },
    [onDocumentSelectAll]
  )

  // 處理單個選擇
  const handleDocumentSelect = useCallback(
    (documentId: string) => {
      onDocumentSelect?.(documentId)
    },
    [onDocumentSelect]
  )

  if (loading) {
    return (
      <div className={cn("space-y-4", className)}>
        {/* 載入骨架 */}
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="flex items-center space-x-4 p-4 bg-white border rounded-lg">
              <div className="w-4 h-4 bg-gray-200 rounded" />
              <div className="w-8 h-8 bg-gray-200 rounded" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/3" />
                <div className="h-3 bg-gray-200 rounded w-1/4" />
              </div>
              <div className="w-20 h-6 bg-gray-200 rounded" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* 工具列 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        {/* 搜尋和篩選 */}
        <div className="flex items-center space-x-4">
          {/* 搜尋框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜尋文檔..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 狀態篩選 */}
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as DocumentStatus | "all")
            }
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <option value="all">所有狀態</option>
            <option value="queued">排隊中</option>
            <option value="processing">處理中</option>
            <option value="completed">已完成</option>
            <option value="failed">失敗</option>
            <option value="cancelled">已取消</option>
          </select>

          {/* 分類篩選 */}
          {categories.length > 0 && (
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option value="all">所有分類</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* 檢視模式切換 */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onViewModeChange?.("list")}
            className={cn(
              "p-2 rounded-lg",
              viewMode === "list"
                ? "bg-blue-100 text-blue-600"
                : "text-gray-400 hover:text-gray-600"
            )}>
            <List className="h-4 w-4" />
          </button>
          <button
            onClick={() => onViewModeChange?.("grid")}
            className={cn(
              "p-2 rounded-lg",
              viewMode === "grid"
                ? "bg-blue-100 text-blue-600"
                : "text-gray-400 hover:text-gray-600"
            )}>
            <Grid className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* 批次操作列 */}
      {selectedDocuments.length > 0 && (
        <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <span className="text-sm text-blue-700">
            已選擇 {selectedDocuments.length} 個文檔
          </span>
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1 text-sm text-blue-600 hover:text-blue-500">
              批次下載
            </button>
            <button className="px-3 py-1 text-sm text-red-600 hover:text-red-500">
              批次刪除
            </button>
          </div>
        </div>
      )}

      {/* 文檔列表 */}
      {filteredDocuments.length === 0 ? (
        <div className="text-center py-12">
          <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            沒有找到文檔
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery || statusFilter !== "all" || categoryFilter !== "all"
              ? "嘗試調整搜尋條件或篩選器"
              : "開始上傳您的第一個文檔"}
          </p>
        </div>
      ) : (
        <div
          className={cn(
            viewMode === "grid"
              ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
              : "space-y-2"
          )}>
          {/* 表頭 (僅列表模式) */}
          {viewMode === "list" && (
            <div className="flex items-center space-x-4 px-4 py-2 bg-gray-50 border rounded-lg text-sm font-medium text-gray-700">
              <input
                type="checkbox"
                checked={selectedDocuments.length === filteredDocuments.length}
                onChange={(e) => handleSelectAll(e.target.checked)}
                className="rounded border-gray-300"
              />
              <div className="flex-1 grid grid-cols-12 gap-4">
                <div className="col-span-4">檔案名稱</div>
                <div className="col-span-2">狀態</div>
                <div className="col-span-2">分類</div>
                <div className="col-span-2">大小</div>
                <div className="col-span-2">上傳時間</div>
              </div>
              <div className="w-8">操作</div>
            </div>
          )}

          {/* 文檔項目 */}
          {filteredDocuments.map((document) => (
            <DocumentItem
              key={document.id}
              document={document}
              viewMode={viewMode}
              isSelected={selectedDocuments.includes(document.id)}
              onSelect={() => handleDocumentSelect(document.id)}
              onView={() => onDocumentView?.(document)}
              onEdit={() => onDocumentEdit?.(document)}
              onDownload={() => onDocumentDownload?.(document)}
              onDelete={() => onDocumentDelete?.(document)}
              formatFileSize={formatFileSize}
              formatDate={formatDate}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// 單個文檔項目組件
interface DocumentItemProps {
  document: DocumentMetadata
  viewMode: "grid" | "list"
  isSelected: boolean
  onSelect: () => void
  onView: () => void
  onEdit: () => void
  onDownload: () => void
  onDelete: () => void
  formatFileSize: (bytes: number) => string
  formatDate: (date: string) => string
}

function DocumentItem({
  document,
  viewMode,
  isSelected,
  onSelect,
  onView,
  onEdit,
  onDownload,
  onDelete,
  formatFileSize,
  formatDate,
}: DocumentItemProps) {
  const [showMenu, setShowMenu] = useState(false)
  const fileIcon =
    fileTypeIcons[document.file_type as keyof typeof fileTypeIcons] ||
    fileTypeIcons.default

  if (viewMode === "grid") {
    return (
      <div
        className={cn(
          "relative p-4 bg-white border rounded-lg hover:shadow-md transition-shadow cursor-pointer",
          isSelected && "ring-2 ring-blue-500 border-blue-500"
        )}>
        {/* 選擇框 */}
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onSelect}
          className="absolute top-3 left-3 rounded border-gray-300"
          onClick={(e) => e.stopPropagation()}
        />

        {/* 操作選單 */}
        <div className="absolute top-3 right-3">
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowMenu(!showMenu)
            }}
            className="p-1 text-gray-400 hover:text-gray-600">
            <MoreVertical className="h-4 w-4" />
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-1 w-32 bg-white border rounded-lg shadow-lg z-10">
              <button
                onClick={onView}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50">
                <Eye className="inline h-3 w-3 mr-2" />
                檢視
              </button>
              <button
                onClick={onEdit}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50">
                <Edit className="inline h-3 w-3 mr-2" />
                編輯
              </button>
              <button
                onClick={onDownload}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50">
                <Download className="inline h-3 w-3 mr-2" />
                下載
              </button>
              <button
                onClick={onDelete}
                className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-gray-50">
                <Trash2 className="inline h-3 w-3 mr-2" />
                刪除
              </button>
            </div>
          )}
        </div>

        <div onClick={onView} className="mt-6 space-y-3">
          {/* 檔案圖標和名稱 */}
          <div className="text-center">
            <div className="text-3xl mb-2">{fileIcon}</div>
            <h3
              className="font-medium text-gray-900 truncate"
              title={document.filename}>
              {document.filename}
            </h3>
          </div>

          {/* 狀態 */}
          <div className="flex justify-center">
            <ProcessingStatusBadge
              status={document.status as DocumentStatus}
              progress={document.processing_progress}
            />
          </div>

          {/* 詳細資訊 */}
          <div className="space-y-1 text-xs text-gray-500">
            <div className="flex items-center justify-between">
              <span>大小</span>
              <span>{formatFileSize(document.file_size)}</span>
            </div>
            {document.category && (
              <div className="flex items-center justify-between">
                <span>分類</span>
                <span className="truncate ml-2">{document.category}</span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span>上傳</span>
              <span>{formatDate(document.created_at)}</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 列表模式
  return (
    <div
      className={cn(
        "flex items-center space-x-4 p-4 bg-white border rounded-lg hover:shadow-sm transition-shadow",
        isSelected && "ring-2 ring-blue-500 border-blue-500"
      )}>
      <input
        type="checkbox"
        checked={isSelected}
        onChange={onSelect}
        className="rounded border-gray-300"
      />

      <div className="flex-1 grid grid-cols-12 gap-4 items-center">
        {/* 檔案名稱 */}
        <div className="col-span-4 flex items-center space-x-3">
          <span className="text-lg">{fileIcon}</span>
          <div className="min-w-0">
            <p className="font-medium text-gray-900 truncate">
              {document.filename}
            </p>
            {document.description && (
              <p className="text-sm text-gray-500 truncate">
                {document.description}
              </p>
            )}
          </div>
        </div>

        {/* 狀態 */}
        <div className="col-span-2">
          <ProcessingStatusBadge
            status={document.status as DocumentStatus}
            progress={document.processing_progress}
          />
        </div>

        {/* 分類 */}
        <div className="col-span-2">
          {document.category ? (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              <Tag className="h-3 w-3 mr-1" />
              {document.category}
            </span>
          ) : (
            <span className="text-sm text-gray-400">無分類</span>
          )}
        </div>

        {/* 檔案大小 */}
        <div className="col-span-2 text-sm text-gray-600">
          {formatFileSize(document.file_size)}
        </div>

        {/* 上傳時間 */}
        <div className="col-span-2 text-sm text-gray-600">
          {formatDate(document.created_at)}
        </div>
      </div>

      {/* 操作選單 */}
      <div className="relative">
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="p-1 text-gray-400 hover:text-gray-600">
          <MoreVertical className="h-4 w-4" />
        </button>

        {showMenu && (
          <div className="absolute right-0 mt-1 w-32 bg-white border rounded-lg shadow-lg z-10">
            <button
              onClick={onView}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50">
              <Eye className="inline h-3 w-3 mr-2" />
              檢視
            </button>
            <button
              onClick={onEdit}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50">
              <Edit className="inline h-3 w-3 mr-2" />
              編輯
            </button>
            <button
              onClick={onDownload}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50">
              <Download className="inline h-3 w-3 mr-2" />
              下載
            </button>
            <button
              onClick={onDelete}
              className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-gray-50">
              <Trash2 className="inline h-3 w-3 mr-2" />
              刪除
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
