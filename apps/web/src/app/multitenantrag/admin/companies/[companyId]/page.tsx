"use client"

import React, { useState, useCallback } from "react"
import { useParams } from "next/navigation"
import {
  ArrowLeft,
  Edit,
  Settings,
  Users,
  BarChart3,
  Power,
  PowerOff,
  Trash2,
  Building2,
  FileText,
  type LucideIcon,
} from "lucide-react"
import Link from "next/link"
import Image from "next/image"
import { CompanyStatsCard } from "@/components/companies/CompanyStatsCard"
import { CompanyUserManagement } from "@/components/companies/CompanyUserManagement"
import { CompanyForm } from "@/components/companies/CompanyForm"
import { DocumentUpload } from "@/components/documents/DocumentUpload"
import { DocumentList } from "@/components/documents/DocumentList"
import {
  useCompany,
  useCompanyStats,
  useCompanyUsers,
  useCompanyOperations,
} from "@/hooks/useCompanies"
import type { UpdateCompanyRequest, InviteUserRequest } from "@/types/company"
import { cn } from "@/lib/utils"

export default function CompanyDetailPage() {
  const params = useParams()
  const companyId = params.companyId as string

  // 狀態管理
  type TabType = "overview" | "documents" | "users" | "settings"
  const [activeTab, setActiveTab] = useState<TabType>("overview")
  const [showEditForm, setShowEditForm] = useState(false)

  // API hooks
  const {
    company,
    loading: companyLoading,
    error: companyError,
    refresh: refreshCompany,
  } = useCompany(companyId)
  const {
    stats,
    loading: statsLoading,
    refresh: refreshStats,
  } = useCompanyStats(companyId)
  const {
    users,
    inviteUser,
    removeUser,
    updateUserRole,
    loading: usersLoading,
    refresh: refreshUsers,
  } = useCompanyUsers(companyId)

  const {
    updateCompany,
    deleteCompany,
    activateCompany,
    deactivateCompany,
    loading: operationLoading,
  } = useCompanyOperations()

  // 處理更新公司
  const handleUpdateCompany = useCallback(
    async (data: UpdateCompanyRequest) => {
      try {
        await updateCompany(companyId, data)
        setShowEditForm(false)
        refreshCompany()
      } catch (error) {
        throw error
      }
    },
    [companyId, updateCompany, refreshCompany]
  )

  // 處理公司狀態切換
  const handleToggleCompanyStatus = useCallback(async () => {
    if (!company) return

    const action = company.is_active ? "停用" : "啟用"
    if (!confirm(`確定要${action}公司 "${company.name}" 嗎？`)) {
      return
    }

    try {
      if (company.is_active) {
        await deactivateCompany(companyId)
      } else {
        await activateCompany(companyId)
      }
      refreshCompany()
    } catch (error) {
      console.error(`${action}公司失敗:`, error)
    }
  }, [company, companyId, activateCompany, deactivateCompany, refreshCompany])

  // 處理刪除公司
  const handleDeleteCompany = useCallback(async () => {
    if (!company) return

    if (!confirm(`確定要刪除公司 "${company.name}" 嗎？此操作無法復原。`)) {
      return
    }

    try {
      await deleteCompany(companyId)
      // 刪除成功後導航回公司列表
      window.location.href = "/multitenantrag/admin/companies"
    } catch (error) {
      console.error("刪除公司失敗:", error)
    }
  }, [company, companyId, deleteCompany])

  // 處理邀請用戶
  const handleInviteUser = useCallback(
    async (userData: InviteUserRequest) => {
      await inviteUser(userData)
      refreshUsers()
    },
    [inviteUser, refreshUsers]
  )

  // 處理移除用戶
  const handleRemoveUser = useCallback(
    async (userId: number) => {
      await removeUser(userId)
      refreshUsers()
    },
    [removeUser, refreshUsers]
  )

  // 處理更新用戶角色
  const handleUpdateUserRole = useCallback(
    async (userId: number, role: string) => {
      await updateUserRole(userId, role)
      refreshUsers()
    },
    [updateUserRole, refreshUsers]
  )

  if (companyLoading || (!company && !companyError)) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (companyError || !company) {
    return (
      <div className="text-center py-12">
        <Building2 className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">找不到公司</h3>
        <p className="mt-1 text-sm text-gray-500">
          {companyError || "請檢查公司 ID 是否正確"}
        </p>
        <div className="mt-6">
          <Link
            href="/multitenantrag/admin/companies"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700">
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回公司列表
          </Link>
        </div>
      </div>
    )
  }

  const tabs: Array<{ id: TabType; name: string; icon: LucideIcon }> = [
    { id: "overview", name: "總覽", icon: BarChart3 },
    { id: "documents", name: "文檔管理", icon: FileText },
    { id: "users", name: "用戶管理", icon: Users },
    { id: "settings", name: "設定", icon: Settings },
  ]

  return (
    <div className="space-y-6">
      {/* 頁面標題和操作 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center space-x-4">
          <Link
            href="/multitenantrag/admin/companies"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700">
            <ArrowLeft className="h-4 w-4 mr-1" />
            返回列表
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                {company.logo_url ? (
                  <Image
                    src={company.logo_url}
                    alt={company.name}
                    width={32}
                    height={32}
                    className="w-8 h-8 rounded"
                  />
                ) : (
                  <Building2 className="h-5 w-5 text-blue-600" />
                )}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {company.name}
                </h1>
                <div className="flex items-center space-x-2">
                  <span
                    className={cn(
                      "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
                      company.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    )}>
                    {company.is_active ? (
                      <>
                        <Power className="h-3 w-3 mr-1" />
                        啟用中
                      </>
                    ) : (
                      <>
                        <PowerOff className="h-3 w-3 mr-1" />
                        已停用
                      </>
                    )}
                  </span>
                  <span className="text-sm text-gray-500">
                    建立於{" "}
                    {new Date(company.created_at).toLocaleDateString("zh-TW")}
                  </span>
                </div>
              </div>
            </div>
            {company.description && (
              <p className="mt-2 text-sm text-gray-600">
                {company.description}
              </p>
            )}
          </div>
        </div>

        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <button
            onClick={() => setShowEditForm(true)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            <Edit className="h-4 w-4 mr-2" />
            編輯資訊
          </button>

          <button
            onClick={handleToggleCompanyStatus}
            disabled={operationLoading}
            className={cn(
              "inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white",
              company.is_active
                ? "bg-orange-600 hover:bg-orange-700"
                : "bg-green-600 hover:bg-green-700"
            )}>
            {company.is_active ? (
              <>
                <PowerOff className="h-4 w-4 mr-2" />
                停用公司
              </>
            ) : (
              <>
                <Power className="h-4 w-4 mr-2" />
                啟用公司
              </>
            )}
          </button>

          <button
            onClick={handleDeleteCompany}
            disabled={operationLoading}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700">
            <Trash2 className="h-4 w-4 mr-2" />
            刪除公司
          </button>
        </div>
      </div>

      {/* 編輯表單 */}
      {showEditForm && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-gray-900">編輯公司資訊</h2>
            <button
              onClick={() => setShowEditForm(false)}
              className="text-gray-400 hover:text-gray-600">
              ×
            </button>
          </div>

          <CompanyForm
            company={company}
            onSubmit={handleUpdateCompany}
            onCancel={() => setShowEditForm(false)}
            loading={operationLoading}
          />
        </div>
      )}

      {/* 標籤導航 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center py-2 px-1 border-b-2 font-medium text-sm",
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}>
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* 標籤內容 */}
      <div className="space-y-6">
        {activeTab === "overview" && (
          <CompanyStatsCard
            stats={
              stats || {
                total_users: users.length,
                active_users: users.filter((u) => u.is_active).length,
                total_documents: 0,
                total_conversations: 0,
                monthly_conversations: 0,
                storage_used: 0,
                storage_limit: 1024 * 1024 * 1024, // 1GB default
              }
            }
            loading={statsLoading}
          />
        )}

        {activeTab === "users" && (
          <CompanyUserManagement
            users={users}
            onInviteUser={handleInviteUser}
            onRemoveUser={handleRemoveUser}
            onUpdateUserRole={handleUpdateUserRole}
            loading={usersLoading}
          />
        )}

        {activeTab === "settings" && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">公司設定</h3>
            <p className="text-sm text-gray-500">公司設定功能開發中...</p>
          </div>
        )}
      </div>
    </div>
  )
}
