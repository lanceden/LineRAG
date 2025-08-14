"use client"

import { User } from '@/lib/api/users'
import { useState } from 'react'

interface UserTableProps {
  users: User[]
  loading: boolean
  onEdit: (user: User) => void
  onDelete: (user: User) => void
}

export function UserTable({ users, loading, onEdit, onDelete }: UserTableProps) {
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const getRoleBadge = (role: string) => {
    const roleStyles = {
      super_admin: 'bg-red-100 text-red-800',
      admin: 'bg-blue-100 text-blue-800',
      company_admin: 'bg-green-100 text-green-800',
      cs_manager: 'bg-yellow-100 text-yellow-800',
      cs_agent: 'bg-gray-100 text-gray-800',
    }
    
    const roleNames = {
      super_admin: '超級管理員',
      admin: '管理員',
      company_admin: '公司管理員',
      cs_manager: '客服經理',
      cs_agent: '客服人員',
    }

    return (
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${roleStyles[role as keyof typeof roleStyles] || roleStyles.cs_agent}`}>
        {roleNames[role as keyof typeof roleNames] || role}
      </span>
    )
  }

  const getStatusBadge = (isActive: boolean) => {
    return (
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
        isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}>
        {isActive ? '啟用' : '停用'}
      </span>
    )
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '從未登入'
    
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    
    if (diffMinutes < 5) return '剛剛'
    if (diffMinutes < 60) return `${diffMinutes} 分鐘前`
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)} 小時前`
    
    return date.toLocaleDateString('zh-TW')
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用戶</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">角色</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">可訪問公司</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">狀態</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最後登入</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            <tr>
              <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                <div className="flex flex-col items-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
                  <p className="text-lg font-medium">載入用戶資料中...</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    )
  }

  if (users.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用戶</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">角色</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">可訪問公司</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">狀態</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最後登入</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            <tr>
              <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                <div className="flex flex-col items-center">
                  <svg className="h-12 w-12 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  <p className="text-lg font-medium">沒有找到用戶</p>
                  <p className="text-sm">請嘗試修改搜尋條件或新增用戶</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              用戶
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              角色
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              可訪問公司
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              狀態
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              最後登入
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              操作
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="h-10 w-10 flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                      <span className="text-white font-medium text-sm">
                        {getInitials(user.full_name)}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">
                      {user.full_name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {user.email}
                    </div>
                    <div className="text-xs text-gray-400">
                      @{user.username}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getRoleBadge(user.role)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {user.accessible_companies.length > 0 ? (
                  <div>
                    {user.role === 'super_admin' ? (
                      <span className="text-blue-600 font-medium">所有公司</span>
                    ) : (
                      user.accessible_companies.map(company => (
                        <span key={company.id} className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded mr-1 mb-1">
                          {company.name}
                        </span>
                      ))
                    )}
                    <span className="text-gray-400">({user.accessible_companies.length})</span>
                  </div>
                ) : (
                  <span className="text-gray-400">無權限</span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getStatusBadge(user.is_active)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(user.last_login)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div className="flex items-center space-x-2">
                  <button 
                    onClick={() => onEdit(user)}
                    className="text-blue-600 hover:text-blue-900 transition-colors"
                  >
                    編輯
                  </button>
                  {deleteConfirm === user.id ? (
                    <div className="flex items-center space-x-1">
                      <button 
                        onClick={() => {
                          onDelete(user)
                          setDeleteConfirm(null)
                        }}
                        className="text-red-600 hover:text-red-900 text-xs bg-red-50 px-2 py-1 rounded"
                      >
                        確認
                      </button>
                      <button 
                        onClick={() => setDeleteConfirm(null)}
                        className="text-gray-600 hover:text-gray-900 text-xs bg-gray-50 px-2 py-1 rounded"
                      >
                        取消
                      </button>
                    </div>
                  ) : (
                    <button 
                      onClick={() => setDeleteConfirm(user.id)}
                      className="text-red-600 hover:text-red-900 transition-colors"
                    >
                      刪除
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}