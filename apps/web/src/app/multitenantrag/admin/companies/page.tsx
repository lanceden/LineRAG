"use client"

import React, { useState, useCallback, useMemo } from "react"
import {
  Plus,
  RefreshCw,
  Download,
  Upload,
  Building2,
  BarChart3,
} from "lucide-react"
import { CompanyList } from "@/components/companies/CompanyList"
import { CompanyForm } from "@/components/companies/CompanyForm"
import { useCompanies, useCompanyOperations } from "@/hooks/useCompanies"
import type {
  Company,
  CreateCompanyRequest,
  UpdateCompanyRequest,
  CompanyListParams,
} from "@/types/company"

export default function CompaniesPage() {
  // 狀態管理
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingCompany, setEditingCompany] = useState<Company | null>(null)
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<boolean | undefined>(
    undefined
  )

  // API hooks
  const companyParams: CompanyListParams = useMemo(() => ({
    page: currentPage,
    limit: 20,
    search: searchQuery || undefined,
    is_active: statusFilter,
    sort_by: "created_at",
    sort_order: "desc",
  }), [currentPage, searchQuery, statusFilter])

  const {
    companies,
    total,
    loading: companiesLoading,
    error: companiesError,
    refresh: refreshCompanies,
  } = useCompanies(companyParams)

  const {
    createCompany,
    updateCompany,
    deleteCompany,
    activateCompany,
    deactivateCompany,
    loading: operationLoading,
    error: operationError,
  } = useCompanyOperations()

  // 處理建立公司
  const handleCreateCompany = useCallback(
    async (data: CreateCompanyRequest | UpdateCompanyRequest) => {
      try {
        // For create mode, data should be a valid CreateCompanyRequest
        await createCompany(data as CreateCompanyRequest)
        setShowCreateForm(false)
        refreshCompanies()
      } catch (error) {
        // 錯誤處理已在 hook 中完成
        throw error
      }
    },
    [createCompany, refreshCompanies]
  )

  // 處理更新公司
  const handleUpdateCompany = useCallback(
    async (data: CreateCompanyRequest | UpdateCompanyRequest) => {
      if (!editingCompany) return

      try {
        // For update mode, data can be partial UpdateCompanyRequest
        await updateCompany(String(editingCompany.id), data as UpdateCompanyRequest)
        setEditingCompany(null)
        refreshCompanies()
      } catch (error) {
        throw error
      }
    },
    [editingCompany, updateCompany, refreshCompanies]
  )

  // 處理公司選擇
  const handleCompanySelect = useCallback((companyId: string) => {
    setSelectedCompanies((prev) =>
      prev.includes(companyId)
        ? prev.filter((id) => id !== companyId)
        : [...prev, companyId]
    )
  }, [])

  // 處理全選
  const handleCompanySelectAll = useCallback(
    (selected: boolean) => {
      setSelectedCompanies(
        selected ? companies.map((company) => String(company.id)) : []
      )
    },
    [companies]
  )

  // 處理公司檢視
  const handleCompanyView = useCallback((company: Company) => {
    // 導航到公司詳情頁面
    window.location.href = `/multitenantrag/admin/companies/${company.id}`
  }, [])

  // 處理公司編輯
  const handleCompanyEdit = useCallback((company: Company) => {
    setEditingCompany(company)
  }, [])

  // 處理公司刪除
  const handleCompanyDelete = useCallback(
    async (company: Company) => {
      if (!confirm(`確定要刪除公司 "${company.name}" 嗎？此操作無法復原。`)) {
        return
      }

      try {
        await deleteCompany(String(company.id))
        refreshCompanies()
      } catch (error) {
        console.error("刪除公司失敗:", error)
      }
    },
    [deleteCompany, refreshCompanies]
  )

  // 處理公司啟用
  const handleCompanyActivate = useCallback(
    async (company: Company) => {
      try {
        await activateCompany(String(company.id))
        refreshCompanies()
      } catch (error) {
        console.error("啟用公司失敗:", error)
      }
    },
    [activateCompany, refreshCompanies]
  )

  // 處理公司停用
  const handleCompanyDeactivate = useCallback(
    async (company: Company) => {
      if (!confirm(`確定要停用公司 "${company.name}" 嗎？`)) {
        return
      }

      try {
        await deactivateCompany(String(company.id))
        refreshCompanies()
      } catch (error) {
        console.error("停用公司失敗:", error)
      }
    },
    [deactivateCompany, refreshCompanies]
  )

  // 處理公司用戶管理
  const handleCompanyUsers = useCallback((company: Company) => {
    window.location.href = `/multitenantrag/admin/companies/${company.id}/users`
  }, [])

  // 處理公司設定
  const handleCompanySettings = useCallback((company: Company) => {
    window.location.href = `/multitenantrag/admin/companies/${company.id}/settings`
  }, [])

  return (
    <div className="space-y-6">
      {/* 頁面標題和操作 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">公司管理</h1>
          <p className="mt-1 text-sm text-gray-500">
            管理系統中的所有公司和組織
          </p>
        </div>

        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          <button
            onClick={() => refreshCompanies()}
            disabled={companiesLoading}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            <RefreshCw
              className={`h-4 w-4 mr-2 ${
                companiesLoading ? "animate-spin" : ""
              }`}
            />
            重新整理
          </button>

          <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            <Download className="h-4 w-4 mr-2" />
            匯出
          </button>

          <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            <Upload className="h-4 w-4 mr-2" />
            匯入
          </button>

          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            <Plus className="h-4 w-4 mr-2" />
            新增公司
          </button>
        </div>
      </div>

      {/* 統計資訊 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Building2 className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    總公司數
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">{total}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3 className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    啟用中
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {companies.filter((c) => c.is_active).length}
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
                <BarChart3 className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    已停用
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {companies.filter((c) => !c.is_active).length}
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
                <BarChart3 className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    本月新增
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {
                      companies.filter((c) => {
                        const createdAt = new Date(c.created_at)
                        const now = new Date()
                        return (
                          createdAt.getMonth() === now.getMonth() &&
                          createdAt.getFullYear() === now.getFullYear()
                        )
                      }).length
                    }
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 建立公司表單 */}
      {showCreateForm && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-gray-900">建立新公司</h2>
            <button
              onClick={() => setShowCreateForm(false)}
              className="text-gray-400 hover:text-gray-600">
              ×
            </button>
          </div>

          <CompanyForm
            onSubmit={handleCreateCompany}
            onCancel={() => setShowCreateForm(false)}
            loading={operationLoading}
          />
        </div>
      )}

      {/* 編輯公司表單 */}
      {editingCompany && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-gray-900">編輯公司資訊</h2>
            <button
              onClick={() => setEditingCompany(null)}
              className="text-gray-400 hover:text-gray-600">
              ×
            </button>
          </div>

          <CompanyForm
            company={editingCompany}
            onSubmit={handleUpdateCompany}
            onCancel={() => setEditingCompany(null)}
            loading={operationLoading}
          />
        </div>
      )}

      {/* 錯誤訊息 */}
      {(companiesError || operationError) && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">發生錯誤</h3>
              <div className="mt-2 text-sm text-red-700">
                {companiesError || operationError}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 公司列表 */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">公司列表</h2>
        </div>

        <div className="p-6">
          <CompanyList
            companies={companies}
            loading={companiesLoading}
            selectedCompanies={selectedCompanies}
            onCompanySelect={handleCompanySelect}
            onCompanySelectAll={handleCompanySelectAll}
            onCompanyView={handleCompanyView}
            onCompanyEdit={handleCompanyEdit}
            onCompanyDelete={handleCompanyDelete}
            onCompanyActivate={handleCompanyActivate}
            onCompanyDeactivate={handleCompanyDeactivate}
            onCompanyUsers={handleCompanyUsers}
            onCompanySettings={handleCompanySettings}
          />
        </div>
      </div>

      {/* 分頁 */}
      {total > 20 && (
        <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 rounded-lg shadow">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50">
              上一頁
            </button>
            <button
              onClick={() => setCurrentPage((prev) => prev + 1)}
              disabled={currentPage * 20 >= total}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50">
              下一頁
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                顯示第{" "}
                <span className="font-medium">
                  {(currentPage - 1) * 20 + 1}
                </span>{" "}
                到{" "}
                <span className="font-medium">
                  {Math.min(currentPage * 20, total)}
                </span>{" "}
                項， 共 <span className="font-medium">{total}</span> 項結果
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(1, prev - 1))
                  }
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50">
                  上一頁
                </button>
                <button
                  onClick={() => setCurrentPage((prev) => prev + 1)}
                  disabled={currentPage * 20 >= total}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50">
                  下一頁
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
