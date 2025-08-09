'use client'

import { usePermissions } from '@/lib/permissions'
import PermissionGuard from '@/components/PermissionGuard'
import Link from 'next/link'

export default function DashboardPage() {
  return (
    <PermissionGuard requiredRole="cs">
      <DashboardContent />
    </PermissionGuard>
  )
}

function DashboardContent() {
  const { user, isAdmin, isCS } = usePermissions()

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            歡迎，{user?.name || '用戶'}
          </h1>
          <p className="mt-2 text-gray-600">
            {isAdmin ? '管理員控制台' : '客服工作台'}
          </p>
        </div>

        {/* User Info Card */}
        <div className="bg-white overflow-hidden shadow rounded-lg mb-8">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              用戶資訊
            </h3>
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">姓名</dt>
                <dd className="mt-1 text-sm text-gray-900">{user?.name || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">角色</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    isAdmin 
                      ? 'bg-purple-100 text-purple-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {isAdmin ? '管理員' : '客服人員'}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">LINE ID</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{user?.lineId}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">狀態</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user?.isActive
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {user?.isActive ? '啟用中' : '已停用'}
                  </span>
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-8">
          
          {/* Chat Panel */}
          <Link href="/chat" className="group">
            <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate group-hover:text-gray-700">
                        測試對話
                      </dt>
                      <dd className="text-lg font-medium text-gray-900 group-hover:text-blue-600">
                        開始聊天
                      </dd>
                    </dl>
                  </div>
                  <div className="ml-4">
                    <div className="text-gray-400 group-hover:text-blue-500">
                      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Link>

          {/* Document Management (Admin only) */}
          {isAdmin && (
            <Link href="/documents" className="group">
              <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate group-hover:text-gray-700">
                          知識庫管理
                        </dt>
                        <dd className="text-lg font-medium text-gray-900 group-hover:text-blue-600">
                          管理文檔
                        </dd>
                      </dl>
                    </div>
                    <div className="ml-4">
                      <div className="text-gray-400 group-hover:text-blue-500">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          )}

          {/* User Management (Admin only) */}
          {isAdmin && (
            <Link href="/admin" className="group">
              <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate group-hover:text-gray-700">
                          用戶管理
                        </dt>
                        <dd className="text-lg font-medium text-gray-900 group-hover:text-blue-600">
                          角色權限
                        </dd>
                      </dl>
                    </div>
                    <div className="ml-4">
                      <div className="text-gray-400 group-hover:text-blue-500">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          )}

          {/* Statistics */}
          <Link href="/stats" className="group">
            <div className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate group-hover:text-gray-700">
                        使用統計
                      </dt>
                      <dd className="text-lg font-medium text-gray-900 group-hover:text-blue-600">
                        查看報表
                      </dd>
                    </dl>
                  </div>
                  <div className="ml-4">
                    <div className="text-gray-400 group-hover:text-blue-500">
                      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Link>

        </div>

        {/* Role-based Information */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">
            {isAdmin ? '管理員功能' : '客服功能'}
          </h3>
          <div className="text-sm text-blue-700">
            {isAdmin ? (
              <ul className="space-y-1">
                <li>• 管理知識庫文檔（上傳、刪除）</li>
                <li>• 管理用戶角色與權限</li>
                <li>• 查看完整系統統計</li>
                <li>• 測試AI對話功能</li>
                <li>• 系統設定與配置</li>
              </ul>
            ) : (
              <ul className="space-y-1">
                <li>• 查看客戶對話記錄</li>
                <li>• 使用AI對話測試</li>
                <li>• 查看基礎統計資料</li>
                <li>• 協助客戶問題解答</li>
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}