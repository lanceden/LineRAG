'use client'

import React from 'react'
import { 
  Users, 
  FileText, 
  MessageSquare, 
  HardDrive,
  TrendingUp,
  Calendar,
  Activity
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CompanyStats } from '@/types/company'

interface CompanyStatsCardProps {
  stats: CompanyStats
  loading?: boolean
  className?: string
}

export function CompanyStatsCard({ stats, loading = false, className }: CompanyStatsCardProps) {
  // 格式化檔案大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 計算儲存使用率
  const storageUsagePercent = stats.storage_limit > 0 
    ? Math.round((stats.storage_used / stats.storage_limit) * 100)
    : 0

  if (loading) {
    return (
      <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4', className)}>
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="animate-pulse bg-white p-6 rounded-lg border">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-200 rounded"></div>
              <div className="ml-4 flex-1">
                <div className="h-4 bg-gray-200 rounded w-16 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-12"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const statsCards = [
    {
      title: '總用戶數',
      value: stats.total_users,
      subtitle: `${stats.active_users} 位活躍用戶`,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: '文檔數量',
      value: stats.total_documents,
      subtitle: '知識庫文檔',
      icon: FileText,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: '對話數量',
      value: stats.total_conversations,
      subtitle: `本月 ${stats.monthly_conversations} 次`,
      icon: MessageSquare,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: '儲存使用',
      value: formatFileSize(stats.storage_used),
      subtitle: `${storageUsagePercent}% / ${formatFileSize(stats.storage_limit)}`,
      icon: HardDrive,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ]

  return (
    <div className={cn('space-y-6', className)}>
      {/* 統計卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map((card, index) => (
          <div key={index} className="bg-white p-6 rounded-lg border hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className={cn('p-2 rounded-lg', card.bgColor)}>
                <card.icon className={cn('h-6 w-6', card.color)} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                <p className="text-xs text-gray-500">{card.subtitle}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 詳細統計 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 用戶活動 */}
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center mb-4">
            <Activity className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">用戶活動</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">總用戶數</span>
              <span className="font-medium">{stats.total_users}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">活躍用戶</span>
              <span className="font-medium text-green-600">{stats.active_users}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">活躍率</span>
              <span className="font-medium">
                {stats.total_users > 0 
                  ? Math.round((stats.active_users / stats.total_users) * 100)
                  : 0}%
              </span>
            </div>
          </div>
        </div>

        {/* 儲存使用情況 */}
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center mb-4">
            <HardDrive className="h-5 w-5 text-orange-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">儲存使用</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">已使用</span>
              <span className="font-medium">{formatFileSize(stats.storage_used)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">總容量</span>
              <span className="font-medium">{formatFileSize(stats.storage_limit)}</span>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">使用率</span>
                <span className={cn(
                  'font-medium',
                  storageUsagePercent > 80 ? 'text-red-600' :
                  storageUsagePercent > 60 ? 'text-orange-600' : 'text-green-600'
                )}>
                  {storageUsagePercent}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={cn(
                    'h-2 rounded-full transition-all duration-300',
                    storageUsagePercent > 80 ? 'bg-red-500' :
                    storageUsagePercent > 60 ? 'bg-orange-500' : 'bg-green-500'
                  )}
                  style={{ width: `${Math.min(storageUsagePercent, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 對話統計 */}
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center mb-4">
            <MessageSquare className="h-5 w-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">對話統計</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">總對話數</span>
              <span className="font-medium">{stats.total_conversations}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">本月對話</span>
              <span className="font-medium text-purple-600">{stats.monthly_conversations}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">平均每日</span>
              <span className="font-medium">
                {Math.round(stats.monthly_conversations / 30)} 次
              </span>
            </div>
          </div>
        </div>

        {/* 最後活動 */}
        <div className="bg-white p-6 rounded-lg border">
          <div className="flex items-center mb-4">
            <Calendar className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">活動記錄</h3>
          </div>
          <div className="space-y-3">
            {stats.last_activity ? (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">最後活動</span>
                  <span className="font-medium">
                    {new Date(stats.last_activity).toLocaleString('zh-TW')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">狀態</span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1"></div>
                    活躍中
                  </span>
                </div>
              </>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-gray-500">尚無活動記錄</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 趨勢指標 */}
      <div className="bg-white p-6 rounded-lg border">
        <div className="flex items-center mb-4">
          <TrendingUp className="h-5 w-5 text-green-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">成長趨勢</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              +{Math.round((stats.active_users / Math.max(stats.total_users, 1)) * 100)}%
            </p>
            <p className="text-sm text-gray-600">用戶活躍率</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {stats.monthly_conversations}
            </p>
            <p className="text-sm text-gray-600">本月對話數</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">
              {stats.total_documents}
            </p>
            <p className="text-sm text-gray-600">知識庫文檔</p>
          </div>
        </div>
      </div>
    </div>
  )
}
