'use client'

import { useState, useEffect } from 'react'
import { usePermissions, User, fetchUsers, updateUserRole, deactivateUser } from '@/lib/permissions'
import PermissionGuard from '@/components/PermissionGuard'

export default function AdminPage() {
  return (
    <PermissionGuard requiredRole="admin">
      <AdminContent />
    </PermissionGuard>
  )
}

function AdminContent() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { user: currentUser } = usePermissions()

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      const data = await fetchUsers()
      setUsers(data)
      setError(null)
    } catch (err) {
      setError('載入用戶列表失敗')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleRoleUpdate = async (lineId: string, newRole: 'admin' | 'cs') => {
    try {
      await updateUserRole(lineId, newRole)
      await loadUsers() // 重新載入列表
      alert('角色更新成功')
    } catch (err) {
      alert('角色更新失敗')
      console.error(err)
    }
  }

  const handleDeactivate = async (lineId: string) => {
    if (!confirm('確定要停用此用戶嗎？')) return
    
    try {
      await deactivateUser(lineId)
      await loadUsers() // 重新載入列表
      alert('用戶已停用')
    } catch (err) {
      alert('停用失敗')
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3">載入中...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">用戶管理</h1>
          <p className="mt-2 text-gray-600">管理系統用戶角色與權限</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* User Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      總用戶數
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {users.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      管理員
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {users.filter(u => u.role === 'admin').length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      客服人員
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {users.filter(u => u.role === 'cs').length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              用戶列表
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              管理所有系統用戶的角色與狀態
            </p>
          </div>
          
          <ul className="divide-y divide-gray-200">
            {users.map((user) => (
              <li key={user.line_id}>
                <div className="px-4 py-4 flex items-center justify-between">
                  <div className="flex items-center min-w-0 flex-1">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {user.name}
                        </p>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          user.role === 'admin' 
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {user.role === 'admin' ? '管理員' : '客服'}
                        </span>
                        {!user.is_active && (
                          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            已停用
                          </span>
                        )}
                      </div>
                      <div className="flex items-center mt-1">
                        <p className="text-sm text-gray-500 truncate">
                          LINE ID: {user.line_id}
                        </p>
                        {user.email && (
                          <p className="ml-4 text-sm text-gray-500 truncate">
                            {user.email}
                          </p>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        建立時間: {new Date(user.created_at * 1000).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {user.line_id !== currentUser?.lineId && user.is_active && (
                      <>
                        <select
                          value={user.role}
                          onChange={(e) => handleRoleUpdate(user.line_id, e.target.value as 'admin' | 'cs')}
                          className="text-sm border border-gray-300 rounded px-2 py-1"
                        >
                          <option value="cs">客服</option>
                          <option value="admin">管理員</option>
                        </select>
                        
                        <button
                          onClick={() => handleDeactivate(user.line_id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          停用
                        </button>
                      </>
                    )}
                    
                    {user.line_id === currentUser?.lineId && (
                      <span className="text-sm text-gray-500">(目前用戶)</span>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}