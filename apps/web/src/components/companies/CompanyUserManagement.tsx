'use client'

import React, { useState, useCallback } from 'react'
import { 
  Users, 
  UserPlus, 
  Mail, 
  MoreVertical, 
  Edit, 
  Trash2, 
  Shield,
  Clock,
  CheckCircle,
  XCircle,
  Send
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CompanyUser, InviteUserRequest, CompanyInvitation } from '@/types/company'

interface CompanyUserManagementProps {
  users: CompanyUser[]
  invitations?: CompanyInvitation[]
  onInviteUser: (userData: InviteUserRequest) => Promise<void>
  onRemoveUser: (userId: number) => Promise<void>
  onUpdateUserRole: (userId: number, role: string) => Promise<void>
  onCancelInvitation?: (invitationId: string) => Promise<void>
  onResendInvitation?: (invitationId: string) => Promise<void>
  loading?: boolean
  className?: string
}

export function CompanyUserManagement({
  users,
  invitations = [],
  onInviteUser,
  onRemoveUser,
  onUpdateUserRole,
  onCancelInvitation,
  onResendInvitation,
  loading = false,
  className,
}: CompanyUserManagementProps) {
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteData, setInviteData] = useState<InviteUserRequest>({
    email: '',
    name: '',
    role: 'cs_agent',
  })
  const [inviteLoading, setInviteLoading] = useState(false)

  // 角色選項
  const roleOptions = [
    { value: 'company_admin', label: '公司管理員', description: '完整的公司管理權限' },
    { value: 'cs_manager', label: '客服主管', description: '客服團隊管理權限' },
    { value: 'cs_agent', label: '客服專員', description: '基本客服操作權限' },
  ]

  // 處理邀請用戶
  const handleInviteUser = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!inviteData.email || !inviteData.name) {
      return
    }

    setInviteLoading(true)
    try {
      await onInviteUser(inviteData)
      setInviteData({ email: '', name: '', role: 'cs_agent' })
      setShowInviteForm(false)
    } catch (error) {
      // 錯誤處理由父組件負責
    } finally {
      setInviteLoading(false)
    }
  }, [inviteData, onInviteUser])

  // 格式化日期
  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }, [])

  // 獲取角色標籤
  const getRoleLabel = useCallback((role: string) => {
    const option = roleOptions.find(opt => opt.value === role)
    return option?.label || role
  }, [])

  return (
    <div className={cn('space-y-6', className)}>
      {/* 標題和邀請按鈕 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Users className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">用戶管理</h3>
          <span className="ml-2 text-sm text-gray-500">
            ({users.length} 位用戶)
          </span>
        </div>
        <button
          onClick={() => setShowInviteForm(true)}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <UserPlus className="h-4 w-4 mr-2" />
          邀請用戶
        </button>
      </div>

      {/* 邀請表單 */}
      {showInviteForm && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">邀請新用戶</h4>
          <form onSubmit={handleInviteUser} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  姓名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={inviteData.name}
                  onChange={(e) => setInviteData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="請輸入用戶姓名"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  電子郵件 <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="user@example.com"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                角色
              </label>
              <select
                value={inviteData.role}
                onChange={(e) => setInviteData(prev => ({ ...prev, role: e.target.value as any }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {roleOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label} - {option.description}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowInviteForm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={inviteLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {inviteLoading ? '發送中...' : '發送邀請'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* 待處理邀請 */}
      {invitations.length > 0 && (
        <div className="bg-white border rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h4 className="text-lg font-medium text-gray-900">待處理邀請</h4>
          </div>
          <div className="divide-y divide-gray-200">
            {invitations.map((invitation) => (
              <div key={invitation.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                    <Mail className="h-4 w-4 text-yellow-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{invitation.name}</p>
                    <p className="text-sm text-gray-500">{invitation.email}</p>
                    <p className="text-xs text-gray-400">
                      邀請於 {formatDate(invitation.invited_at)} • 
                      到期時間 {formatDate(invitation.expires_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    <Clock className="h-3 w-3 mr-1" />
                    待接受
                  </span>
                  <div className="flex items-center space-x-1">
                    {onResendInvitation && (
                      <button
                        onClick={() => onResendInvitation(invitation.id)}
                        className="p-1 text-blue-600 hover:text-blue-500"
                        title="重新發送邀請"
                      >
                        <Send className="h-4 w-4" />
                      </button>
                    )}
                    {onCancelInvitation && (
                      <button
                        onClick={() => onCancelInvitation(invitation.id)}
                        className="p-1 text-red-600 hover:text-red-500"
                        title="取消邀請"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 現有用戶列表 */}
      <div className="bg-white border rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h4 className="text-lg font-medium text-gray-900">現有用戶</h4>
        </div>
        {users.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">尚無用戶</h3>
            <p className="mt-1 text-sm text-gray-500">開始邀請用戶加入您的公司</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {users.map((user) => (
              <UserItem
                key={user.id}
                user={user}
                roleOptions={roleOptions}
                onUpdateRole={(role) => onUpdateUserRole(user.id, role)}
                onRemove={() => onRemoveUser(user.id)}
                formatDate={formatDate}
                getRoleLabel={getRoleLabel}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// 單個用戶項目組件
interface UserItemProps {
  user: CompanyUser
  roleOptions: Array<{ value: string; label: string; description: string }>
  onUpdateRole: (role: string) => void
  onRemove: () => void
  formatDate: (date: string) => string
  getRoleLabel: (role: string) => string
}

function UserItem({ user, roleOptions, onUpdateRole, onRemove, formatDate, getRoleLabel }: UserItemProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [showRoleEdit, setShowRoleEdit] = useState(false)

  return (
    <div className="px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className={cn(
          'w-10 h-10 rounded-full flex items-center justify-center text-white font-medium',
          user.is_active ? 'bg-green-500' : 'bg-gray-400'
        )}>
          {user.name.charAt(0).toUpperCase()}
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <p className="font-medium text-gray-900">{user.name}</p>
            {user.is_active ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <XCircle className="h-4 w-4 text-gray-400" />
            )}
          </div>
          <p className="text-sm text-gray-500">{user.email}</p>
          <div className="flex items-center space-x-4 text-xs text-gray-400">
            <span>加入時間：{formatDate(user.created_at)}</span>
            {user.last_login && (
              <span>最後登入：{formatDate(user.last_login)}</span>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-3">
        {/* 角色標籤 */}
        <div className="flex items-center space-x-2">
          <Shield className="h-4 w-4 text-gray-400" />
          {showRoleEdit ? (
            <select
              value={user.role}
              onChange={(e) => {
                onUpdateRole(e.target.value)
                setShowRoleEdit(false)
              }}
              onBlur={() => setShowRoleEdit(false)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
              autoFocus
            >
              {roleOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <button
              onClick={() => setShowRoleEdit(true)}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              {getRoleLabel(user.role)}
            </button>
          )}
        </div>

        {/* 操作選單 */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          
          {showMenu && (
            <>
              <div 
                className="fixed inset-0 z-10" 
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 mt-1 w-32 bg-white border rounded-lg shadow-lg z-20">
                <button
                  onClick={() => {
                    setShowRoleEdit(true)
                    setShowMenu(false)
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center"
                >
                  <Edit className="h-3 w-3 mr-2" />
                  編輯角色
                </button>
                <button
                  onClick={() => {
                    if (confirm(`確定要移除用戶 "${user.name}" 嗎？`)) {
                      onRemove()
                    }
                    setShowMenu(false)
                  }}
                  className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-gray-50 flex items-center"
                >
                  <Trash2 className="h-3 w-3 mr-2" />
                  移除用戶
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
