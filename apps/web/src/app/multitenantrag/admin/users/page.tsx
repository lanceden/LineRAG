"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { redirect } from "next/navigation"
import { Sidebar } from "@/components/Sidebar"
import { UserTable } from "@/components/users/UserTable"
import { UserDialog } from "@/components/users/UserDialog"
import { useUsers, useUserStats, useUserActions } from "@/hooks/useUsers"
import { User, CreateUserRequest, UpdateUserRequest } from "@/lib/api/users"

export default function UsersPage() {
  const { data: session, status } = useSession()

  // 增加調試日誌
  console.log('UsersPage render - session:', session, 'status:', status)
  const [searchTerm, setSearchTerm] = useState("")
  const [roleFilter, setRoleFilter] = useState("")
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [successMessage, setSuccessMessage] = useState("")
  const [errorMessage, setErrorMessage] = useState("")

  // 權限檢查
  useEffect(() => {
    if (session && session.user.role !== 'super_admin') {
      window.location.href = "/multitenantrag/auth/login"
    }
  }, [session])

  // API hooks
  const { data: usersData, loading: usersLoading, refetch: refetchUsers } = useUsers({
    search: searchTerm,
    role: roleFilter || undefined,
  })
  
  const { data: statsData, loading: statsLoading, refetch: refetchStats } = useUserStats()
  
  const { loading: actionLoading, createUser, updateUser, deleteUser } = useUserActions()

  // 如果沒有權限，不渲染內容
  if (session && session.user.role !== 'super_admin') {
    return null
  }

  // 處理訊息自動清除
  useEffect(() => {
    if (successMessage || errorMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage("")
        setErrorMessage("")
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [successMessage, errorMessage])

  // 處理用戶操作
  const handleCreateUser = () => {
    setEditingUser(null)
    setDialogOpen(true)
  }

  const handleEditUser = (user: User) => {
    setEditingUser(user)
    setDialogOpen(true)
  }

  const handleDeleteUser = async (user: User) => {
    if (await deleteUser(user.id)) {
      setSuccessMessage(`用戶 ${user.full_name} 已成功刪除`)
      refetchUsers()
      refetchStats()
    } else {
      setErrorMessage("刪除用戶失敗，請稍後再試")
    }
  }

  const handleSubmitUser = async (data: CreateUserRequest | UpdateUserRequest) => {
    try {
      if (editingUser) {
        // 編輯用戶
        const result = await updateUser(editingUser.id, data as UpdateUserRequest)
        if (result) {
          setSuccessMessage(`用戶 ${result.full_name} 已成功更新`)
          setDialogOpen(false)
          refetchUsers()
          refetchStats()
        }
      } else {
        // 創建用戶
        const result = await createUser(data as CreateUserRequest)
        if (result) {
          setSuccessMessage(`用戶 ${result.full_name} 已成功創建`)
          setDialogOpen(false)
          refetchUsers()
          refetchStats()
        }
      }
    } catch (error) {
      setErrorMessage(editingUser ? "更新用戶失敗" : "創建用戶失敗")
    }
  }

  return (
    <>
      <Sidebar />
      <div className="ml-64 p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="border-b border-gray-200 pb-4">
            <h1 className="text-3xl font-bold text-gray-900">用戶管理</h1>
            <p className="mt-2 text-gray-600">
              管理系統中的所有用戶帳號和權限
            </p>
          </div>

          {/* 訊息顯示 */}
          {successMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">{successMessage}</p>
                </div>
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-800">{errorMessage}</p>
                </div>
              </div>
            </div>
          )}

          {/* Actions Bar */}
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="搜尋用戶..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>
              <select 
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">所有角色</option>
                <option value="super_admin">超級管理員</option>
                <option value="admin">管理員</option>
                <option value="company_admin">公司管理員</option>
                <option value="cs_manager">客服經理</option>
                <option value="cs_agent">客服人員</option>
              </select>
            </div>
            <button 
              onClick={handleCreateUser}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span>新增用戶</span>
            </button>
          </div>

          {/* Users Table */}
          <UserTable
            users={usersData?.users || []}
            loading={usersLoading}
            onEdit={handleEditUser}
            onDelete={handleDeleteUser}
          />

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">總用戶數</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {statsLoading ? '-' : statsData?.total_users || 0}
                  </p>
                </div>
                <div className="text-blue-500">
                  👥
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">啟用用戶</p>
                  <p className="text-2xl font-bold text-green-600">
                    {statsLoading ? '-' : statsData?.active_users || 0}
                  </p>
                </div>
                <div className="text-green-500">
                  ✅
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">管理員</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {statsLoading ? '-' : statsData?.admin_users || 0}
                  </p>
                </div>
                <div className="text-orange-500">
                  👑
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">本月新增</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {statsLoading ? '-' : statsData?.new_users_this_month || 0}
                  </p>
                </div>
                <div className="text-purple-500">
                  ➕
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* User Dialog */}
      <UserDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleSubmitUser}
        user={editingUser}
        loading={actionLoading}
      />
    </>
  )
}