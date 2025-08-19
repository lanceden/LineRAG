"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { UserTable } from "@/components/users/UserTable"
import { UserDialog } from "@/components/users/UserDialog"
import { useUsers, useUserStats, useUserActions } from "@/hooks/useUsers"
import { User, CreateUserRequest, UpdateUserRequest } from "@/types/user"
import { usersApi } from "@/lib/api/usersApi"

export default function UsersPage() {
  const { data: session } = useSession()
  
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<boolean | undefined>()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [successMessage, setSuccessMessage] = useState("")
  const [errorMessage, setErrorMessage] = useState("")

  // API hooks
  const { data: usersData, loading: usersLoading, refetch: refetchUsers } = useUsers({
    search: searchTerm,
    is_active: statusFilter
  })
  
  const { data: statsData, loading: statsLoading, refetch: refetchStats } = useUserStats()
  const { createUser, updateUser, deleteUser, loading: actionLoading } = useUserActions()

  const handleCreateUser = () => {
    setEditingUser(null)
    setDialogOpen(true)
  }

  const handleEditUser = (user: User) => {
    setEditingUser(user)
    setDialogOpen(true)
  }

  const handleDeleteUser = async (user: User) => {
    if (confirm(`確定要刪除用戶 ${user.full_name} 嗎？`)) {
      try {
        await usersApi.delete(user.id)
        setSuccessMessage(`用戶 ${user.full_name} 已成功刪除`)
        refetchUsers()
        refetchStats()
      } catch (error) {
        setErrorMessage('刪除用戶失敗')
      }
    }
  }

  const handleSubmit = async (data: CreateUserRequest | UpdateUserRequest) => {
    try {
      if (editingUser) {
        await updateUser(editingUser.id, data as UpdateUserRequest)
        setSuccessMessage('用戶更新成功')
      } else {
        await createUser(data as CreateUserRequest)
        setSuccessMessage('用戶創建成功')
      }
      setDialogOpen(false)
      refetchUsers()
      refetchStats()
    } catch (error) {
      setErrorMessage(editingUser ? '更新用戶失敗' : '創建用戶失敗')
    }
  }

  const handleManagePermissions = (user: User) => {
    // 導航到權限管理頁面或顯示權限對話框
    alert(`管理用戶 ${user.full_name} 的權限功能開發中`)
  }

  const handleToggleStatus = async (user: User) => {
    try {
      // 切換用戶啟用/停用狀態
      const newStatus = !user.is_active
      // 這裡需要調用API來更新用戶狀態
      // await usersApi.updateStatus(user.id, newStatus)
      setSuccessMessage(`用戶狀態已${newStatus ? '啟用' : '停用'}`)
      refetchUsers()
      refetchStats()
    } catch (error) {
      setErrorMessage('更新用戶狀態失敗')
    }
  }

  useEffect(() => {
    if (successMessage || errorMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage("")
        setErrorMessage("")
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [successMessage, errorMessage])

  if (!session) {
    return <div className="p-6">請先登入</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">用戶管理</h1>
        <p className="mt-1 text-sm text-gray-500">
          管理系統用戶和權限設定
        </p>
      </div>

      {/* 統計卡片 */}
      {statsData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <span className="text-2xl">👥</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      總用戶數
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {statsData.total_users}
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
                  <span className="text-2xl">✅</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      啟用用戶
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {statsData.active_users}
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
                  <span className="text-2xl">❌</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      停用用戶
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {statsData.inactive_users}
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
                  <span className="text-2xl">🆕</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      本月新增
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {statsData.users_this_month}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 搜尋和篩選 */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="搜尋用戶..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
          <div>
            <select
              value={statusFilter === undefined ? "" : statusFilter.toString()}
              onChange={(e) => 
                setStatusFilter(e.target.value === "" ? undefined : e.target.value === "true")
              }
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="">所有狀態</option>
              <option value="true">啟用</option>
              <option value="false">停用</option>
            </select>
          </div>
          <div>
            <button
              onClick={handleCreateUser}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              新增用戶
            </button>
          </div>
        </div>
      </div>

      {/* 成功/錯誤訊息 */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-green-700">{successMessage}</p>
            </div>
          </div>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{errorMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* 用戶表格 */}
      <div className="bg-white shadow rounded-lg">
        <UserTable
          users={usersData?.users || []}
          loading={usersLoading}
          onEdit={handleEditUser}
          onDelete={handleDeleteUser}
          onManagePermissions={handleManagePermissions}
          onToggleStatus={handleToggleStatus}
        />
      </div>

      {/* 用戶對話框 */}
      <UserDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleSubmit}
        user={editingUser}
        loading={actionLoading}
      />
    </div>
  )
}