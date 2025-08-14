"use client"

import { useState, useEffect } from "react"
import * as Dialog from "@radix-ui/react-dialog"
import { X, AlertCircle, Upload, Plus } from "lucide-react"
import { User, CreateUserRequest, UpdateUserRequest } from "@/lib/api/users"

interface UserDialogProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => Promise<void>
  user?: User | null
  loading?: boolean
}

export function UserDialog({
  isOpen,
  onClose,
  onSubmit,
  user,
  loading = false,
}: UserDialogProps) {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    full_name: "",
    role: "admin",
    is_active: true,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // 編輯模式時填入現有資料
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        password: "", // 編輯時不顯示密碼
        full_name: user.full_name,
        role: user.role,
        is_active: user.is_active,
      })
    } else {
      setFormData({
        username: "",
        email: "",
        password: "",
        full_name: "",
        role: "admin",
        is_active: true,
      })
    }
    setErrors({})
  }, [user, isOpen])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.username.trim()) {
      newErrors.username = "用戶名稱為必填"
    }

    if (!formData.email.trim()) {
      newErrors.email = "電子信箱為必填"
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "請輸入有效的電子信箱"
    }

    if (!user && !formData.password.trim()) {
      newErrors.password = "密碼為必填"
    }

    if (!formData.full_name.trim()) {
      newErrors.full_name = "姓名為必填"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    try {
      if (user) {
        // 編輯模式：如果有輸入新密碼則包含密碼
        const updateData: UpdateUserRequest & { password?: string } = {
          username: formData.username,
          email: formData.email,
          full_name: formData.full_name,
          role: formData.role,
          is_active: formData.is_active,
        }

        // 如果用戶輸入了新密碼，則包含在更新數據中
        if (formData.password.trim()) {
          updateData.password = formData.password
          console.log(
            "Password will be sent for update:",
            formData.password.length,
            "characters"
          )
        } else {
          console.log("No password provided, will not update password")
        }

        console.log("Final update data:", {
          ...updateData,
          password: updateData.password ? "[HIDDEN]" : undefined,
        })
        await onSubmit(updateData)
      } else {
        // 新增模式
        const createData: CreateUserRequest = {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          role: formData.role,
        }
        await onSubmit(createData)
      }
    } catch (error) {
      console.error("Submit error:", error)
    }
  }

  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 max-w-lg w-full -translate-x-1/2 -translate-y-1/2 bg-white p-6 shadow-xl rounded-lg border">
          <div className="flex items-center justify-between">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              {user ? "編輯用戶" : "新增用戶"}
            </Dialog.Title>
            <Dialog.Close className="rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-gray-100 data-[state=open]:text-gray-500">
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </Dialog.Close>
          </div>
          <Dialog.Description className="text-sm text-gray-600 mb-4">
            {user ? "更新用戶資訊和權限設定" : "創建新的系統用戶帳號"}
          </Dialog.Description>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 用戶名稱 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                用戶名稱 *
              </label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    username: e.target.value,
                  }))
                }
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                  errors.username
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300 hover:border-gray-400"
                }`}
                placeholder="請輸入用戶名稱"
              />
              {errors.username && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  {errors.username}
                </p>
              )}
            </div>

            {/* 電子信箱 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                電子信箱 *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, email: e.target.value }))
                }
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                  errors.email
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300 hover:border-gray-400"
                }`}
                placeholder="請輸入電子信箱"
              />
              {errors.email && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  {errors.email}
                </p>
              )}
            </div>

            {/* 密碼 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                密碼 {!user && "*"}
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    password: e.target.value,
                  }))
                }
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                  errors.password
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300 hover:border-gray-400"
                }`}
                placeholder={user ? "留空則不更改密碼" : "請輸入密碼"}
              />
              {errors.password && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  {errors.password}
                </p>
              )}
            </div>

            {/* 姓名 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                姓名 *
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    full_name: e.target.value,
                  }))
                }
                className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
                  errors.full_name
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300 hover:border-gray-400"
                }`}
                placeholder="請輸入真實姓名"
              />
              {errors.full_name && (
                <p className="mt-2 text-sm text-red-600 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  {errors.full_name}
                </p>
              )}
            </div>

            {/* 角色 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                角色
              </label>
              <select
                value={formData.role}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, role: e.target.value }))
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all hover:border-gray-400 bg-white">
                <option value="admin">管理員</option>
                <option value="super_admin">超級管理員</option>
                <option value="company_admin">公司管理員</option>
                <option value="cs_manager">客服經理</option>
                <option value="cs_agent">客服人員</option>
              </select>
            </div>

            {/* 狀態 (僅編輯時顯示) */}
            {user && (
              <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        is_active: e.target.checked,
                      }))
                    }
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700">
                    啟用帳號
                  </span>
                </label>
              </div>
            )}

            {/* 按鈕區域 */}
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto inline-flex justify-center items-center rounded-lg border border-transparent shadow-sm px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-base font-semibold text-white hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    處理中...
                  </div>
                ) : (
                  <>
                    {user ? (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        更新
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4 mr-2" />
                        創建
                      </>
                    )}
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="mt-3 sm:mt-0 w-full sm:w-auto inline-flex justify-center items-center rounded-lg border border-gray-300 shadow-sm px-6 py-3 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                <X className="h-4 w-4 mr-2" />
                取消
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
