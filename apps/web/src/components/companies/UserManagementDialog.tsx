"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Users, Plus, Trash2, UserPlus, AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { companiesApi } from "@/lib/api/companiesApi"
import { Company } from "@/types/company"

interface UserManagementDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  company: Company | null
  onSuccess: () => void
}

interface CompanyUser {
  id: number
  email: string
  name: string
  role: string
  is_active: boolean
  created_at: string
}

export function UserManagementDialog({
  open,
  onOpenChange,
  company,
  onSuccess,
}: UserManagementDialogProps) {
  const [users, setUsers] = useState<CompanyUser[]>([])
  const [newUser, setNewUser] = useState({ name: "", email: "" })
  const [loading, setLoading] = useState(false)
  const [addingUser, setAddingUser] = useState(false)
  const [deleteUser, setDeleteUser] = useState<CompanyUser | null>(null)

  const loadUsers = useCallback(async () => {
    if (!company) return

    try {
      setLoading(true)
      const response = await companiesApi.getUsers(company.id)
      setUsers(response.users)
    } catch (error) {
      console.error("載入用戶列表失敗:", error)
    } finally {
      setLoading(false)
    }
  }, [company])

  useEffect(() => {
    if (company && open) {
      loadUsers()
      setNewUser({ name: "", email: "" })
    }
  }, [company, open, loadUsers])

  const handleAddUser = async () => {
    if (!company || !newUser.name || !newUser.email) return

    try {
      setAddingUser(true)
      await companiesApi.inviteUser(company.id, {
        name: newUser.name,
        email: newUser.email,
        role: "member", // 預設角色
      })

      setNewUser({ name: "", email: "" })
      await loadUsers()
      onSuccess()
    } catch (error) {
      console.error("新增用戶失敗:", error)
    } finally {
      setAddingUser(false)
    }
  }

  const handleDeleteUser = async (user: CompanyUser) => {
    if (!company) return

    try {
      await companiesApi.removeUser(company.id, user.id)
      await loadUsers()
      setDeleteUser(null)
      onSuccess()
    } catch (error) {
      console.error("刪除用戶失敗:", error)
    }
  }

  if (!company) return null

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>👥 用戶管理 - {company.name}</span>
            </DialogTitle>
            <DialogDescription>
              管理 <strong>{company.name}</strong> 的用戶帳號
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* 用戶列表 */}
            <div className="space-y-3">
              <h4 className="font-medium">📋 用戶列表</h4>

              {loading ? (
                <div className="text-center py-4 text-muted-foreground">
                  載入中...
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  暫無用戶
                </div>
              ) : (
                <div className="space-y-2">
                  {users.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium">{user.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {user.email}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs bg-muted px-2 py-1 rounded">
                          {user.role}
                        </span>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => setDeleteUser(user)}>
                          <Trash2 className="h-3 w-3" />
                          刪除
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 新增用戶區域 */}
            <div className="space-y-3 border-t pt-4">
              <h4 className="font-medium flex items-center space-x-2">
                <UserPlus className="h-4 w-4" />
                <span>➕ 新增用戶</span>
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="user_name">姓名 *</Label>
                  <Input
                    id="user_name"
                    placeholder="請輸入姓名"
                    value={newUser.name}
                    onChange={(e) =>
                      setNewUser((prev) => ({ ...prev, name: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="user_email">信箱 *</Label>
                  <Input
                    id="user_email"
                    type="email"
                    placeholder="請輸入信箱"
                    value={newUser.email}
                    onChange={(e) =>
                      setNewUser((prev) => ({ ...prev, email: e.target.value }))
                    }
                  />
                </div>
              </div>

              <Button
                onClick={handleAddUser}
                disabled={addingUser || !newUser.name || !newUser.email}
                className="w-full">
                <Plus className="mr-2 h-4 w-4" />
                {addingUser ? "新增中..." : "新增用戶"}
              </Button>
            </div>

            {/* 權限提示 */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-blue-800 mb-1">💡 重要提醒</p>
                  <p className="text-blue-700">
                    新增用戶後請至<strong>權限設定頁面</strong>
                    調整該用戶的功能權限和公司存取權限
                  </p>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              關閉
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 刪除用戶確認對話框 */}
      <AlertDialog open={!!deleteUser} onOpenChange={() => setDeleteUser(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>確認刪除用戶</AlertDialogTitle>
            <AlertDialogDescription>
              您確定要刪除用戶 <strong>{deleteUser?.name}</strong> 嗎？
              <br />
              此操作無法復原，該用戶將失去對此公司的所有存取權限。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteUser && handleDeleteUser(deleteUser)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              確認刪除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
