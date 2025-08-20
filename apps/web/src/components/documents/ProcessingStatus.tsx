'use client'

import React from 'react'
import { 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  Loader2,
  RefreshCw,
  FileText,
  Eye
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useDocumentStatus } from '@/hooks/useDocuments'
import type { DocumentStatus } from '@/types/document'

interface ProcessingStatusProps {
  documentId: string
  showDetails?: boolean
  onReprocess?: () => void
  onPreview?: () => void
  className?: string
}

const statusConfig = {
  queued: {
    icon: Clock,
    label: '排隊中',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
  },
  processing: {
    icon: Loader2,
    label: '處理中',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  completed: {
    icon: CheckCircle2,
    label: '完成',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
  failed: {
    icon: XCircle,
    label: '失敗',
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
  },
  cancelled: {
    icon: AlertCircle,
    label: '已取消',
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
  },
}

export function ProcessingStatus({
  documentId,
  showDetails = true,
  onReprocess,
  onPreview,
  className,
}: ProcessingStatusProps) {
  const { status, loading, error, refresh } = useDocumentStatus(documentId)

  if (loading && !status) {
    return (
      <div className={cn('flex items-center space-x-2', className)}>
        <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
        <span className="text-sm text-gray-500">載入狀態中...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn('flex items-center space-x-2', className)}>
        <AlertCircle className="h-4 w-4 text-red-500" />
        <span className="text-sm text-red-600">載入失敗：{error}</span>
        <button
          onClick={refresh}
          className="text-xs text-blue-600 hover:text-blue-500"
        >
          重試
        </button>
      </div>
    )
  }

  if (!status) {
    return (
      <div className={cn('flex items-center space-x-2', className)}>
        <AlertCircle className="h-4 w-4 text-gray-400" />
        <span className="text-sm text-gray-500">無狀態資訊</span>
      </div>
    )
  }

  const config = statusConfig[status.status as DocumentStatus] || statusConfig.queued
  const Icon = config.icon

  if (!showDetails) {
    return (
      <div className={cn('flex items-center space-x-2', className)}>
        <Icon 
          className={cn(
            'h-4 w-4',
            config.color,
            status.status === 'processing' && 'animate-spin'
          )} 
        />
        <span className={cn('text-sm font-medium', config.color)}>
          {config.label}
        </span>
        {status.status === 'processing' && (
          <span className="text-xs text-gray-500">
            {Math.round(status.progress)}%
          </span>
        )}
      </div>
    )
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* 狀態標題 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Icon 
            className={cn(
              'h-5 w-5',
              config.color,
              status.status === 'processing' && 'animate-spin'
            )} 
          />
          <span className={cn('font-medium', config.color)}>
            {config.label}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {status.status === 'completed' && onPreview && (
            <button
              onClick={onPreview}
              className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-500"
            >
              <Eye className="h-3 w-3" />
              <span>預覽</span>
            </button>
          )}
          
          {(status.status === 'failed' || status.status === 'cancelled') && onReprocess && (
            <button
              onClick={onReprocess}
              className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-500"
            >
              <RefreshCw className="h-3 w-3" />
              <span>重新處理</span>
            </button>
          )}
          
          <button
            onClick={refresh}
            className="text-xs text-gray-500 hover:text-gray-700"
            disabled={loading}
          >
            <RefreshCw className={cn('h-3 w-3', loading && 'animate-spin')} />
          </button>
        </div>
      </div>

      {/* 進度條 (僅在處理中時顯示) */}
      {status.status === 'processing' && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600">
            <span>處理進度</span>
            <span>{Math.round(status.progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${status.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 狀態詳情卡片 */}
      <div className={cn(
        'p-3 rounded-lg border',
        config.bgColor,
        config.borderColor
      )}>
        <div className="space-y-2">
          {/* 狀態訊息 */}
          <div className="flex items-start space-x-2">
            <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">
                {status.message || '正在處理文檔...'}
              </p>
              
              {/* 錯誤訊息 */}
              {status.error && (
                <p className="text-sm text-red-600 mt-1">
                  錯誤：{status.error}
                </p>
              )}
            </div>
          </div>

          {/* 時間資訊 */}
          <div className="flex justify-between text-xs text-gray-500">
            <span>文檔 ID：{documentId}</span>
            {status.completed_at && (
              <span>
                完成時間：{new Date(status.completed_at).toLocaleString('zh-TW')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 處理階段指示器 (僅在處理中時顯示) */}
      {status.status === 'processing' && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-gray-700">處理階段</h4>
          <div className="flex items-center space-x-2">
            {[
              { label: '上傳', progress: 100 },
              { label: '解析', progress: status.progress > 30 ? 100 : (status.progress * 3.33) },
              { label: '向量化', progress: status.progress > 60 ? 100 : Math.max(0, (status.progress - 30) * 3.33) },
              { label: '索引', progress: status.progress > 90 ? 100 : Math.max(0, (status.progress - 60) * 3.33) },
            ].map((stage, index) => (
              <div key={stage.label} className="flex-1">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>{stage.label}</span>
                  <span>{Math.round(stage.progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div
                    className={cn(
                      'h-1 rounded-full transition-all duration-500',
                      stage.progress === 100 ? 'bg-green-500' : 'bg-blue-500'
                    )}
                    style={{ width: `${stage.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 成功完成的額外資訊 */}
      {status.status === 'completed' && (
        <div className="text-xs text-gray-600 space-y-1">
          <p>✅ 文檔已成功處理並加入知識庫</p>
          <p>📊 現在可以在對話中搜尋此文檔的內容</p>
        </div>
      )}

      {/* 失敗時的建議 */}
      {status.status === 'failed' && (
        <div className="text-xs text-gray-600 space-y-1">
          <p>❌ 文檔處理失敗</p>
          <p>💡 建議：檢查檔案格式是否正確，或嘗試重新上傳</p>
        </div>
      )}
    </div>
  )
}

// 簡化版本的狀態指示器
export function ProcessingStatusBadge({
  status,
  progress,
  className,
}: {
  status: DocumentStatus
  progress?: number
  className?: string
}) {
  const config = statusConfig[status] || statusConfig.queued
  const Icon = config.icon

  return (
    <div className={cn(
      'inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium',
      config.bgColor,
      config.color,
      className
    )}>
      <Icon 
        className={cn(
          'h-3 w-3',
          status === 'processing' && 'animate-spin'
        )} 
      />
      <span>{config.label}</span>
      {status === 'processing' && progress !== undefined && (
        <span className="ml-1">({Math.round(progress)}%)</span>
      )}
    </div>
  )
}
