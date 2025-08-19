"use client"

import React, { useState, useCallback } from "react"
import Image from "next/image"
import {
  Building2,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  Users,
  Settings,
  Eye,
  Power,
  PowerOff,
  Calendar,
  Globe,
  Mail,
  Phone,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { Company } from "@/types/company"

interface CompanyListProps {
  companies: Company[]
  loading?: boolean
  selectedCompanies?: string[]
  onCompanySelect?: (companyId: string) => void
  onCompanySelectAll?: (selected: boolean) => void
  onCompanyView?: (company: Company) => void
  onCompanyEdit?: (company: Company) => void
  onCompanyDelete?: (company: Company) => void
  onCompanyActivate?: (company: Company) => void
  onCompanyDeactivate?: (company: Company) => void
  onCompanyUsers?: (company: Company) => void
  onCompanySettings?: (company: Company) => void
  className?: string
}

export function CompanyList({
  companies,
  loading = false,
  selectedCompanies = [],
  onCompanySelect,
  onCompanySelectAll,
  onCompanyView,
  onCompanyEdit,
  onCompanyDelete,
  onCompanyActivate,
  onCompanyDeactivate,
  onCompanyUsers,
  onCompanySettings,
  className,
}: CompanyListProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<
    "all" | "active" | "inactive"
  >("all")

  // 格式化日期
  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }, [])

  // 過濾公司
  const filteredCompanies = companies.filter((company) => {
    const matchesSearch =
      searchQuery === "" ||
      company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      company.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      company.email?.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && company.is_active) ||
      (statusFilter === "inactive" && !company.is_active)

    return matchesSearch && matchesStatus
  })

  // 處理全選
  const handleSelectAll = useCallback(
    (checked: boolean) => {
      onCompanySelectAll?.(checked)
    },
    [onCompanySelectAll]
  )

  // 處理單個選擇
  const handleCompanySelect = useCallback(
    (companyId: string) => {
      onCompanySelect?.(companyId)
    },
    [onCompanySelect]
  )

  if (loading) {
    return (
      <div className={cn("space-y-4", className)}>
        {/* 載入骨架 */}
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="flex items-center space-x-4 p-6 bg-white border rounded-lg">
              <div className="w-4 h-4 bg-gray-200 rounded" />
              <div className="w-12 h-12 bg-gray-200 rounded-lg" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/3" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
              <div className="w-20 h-6 bg-gray-200 rounded" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* 工具列 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        {/* 搜尋和篩選 */}
        <div className="flex items-center space-x-4">
          {/* 搜尋框 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜尋公司..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 狀態篩選 */}
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as "all" | "active" | "inactive")
            }
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <option value="all">所有狀態</option>
            <option value="active">啟用中</option>
            <option value="inactive">已停用</option>
          </select>
        </div>

        {/* 統計資訊 */}
        <div className="text-sm text-gray-500">
          顯示 {filteredCompanies.length} / {companies.length} 家公司
        </div>
      </div>

      {/* 批次操作列 */}
      {selectedCompanies.length > 0 && (
        <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <span className="text-sm text-blue-700">
            已選擇 {selectedCompanies.length} 家公司
          </span>
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1 text-sm text-blue-600 hover:text-blue-500">
              批次啟用
            </button>
            <button className="px-3 py-1 text-sm text-orange-600 hover:text-orange-500">
              批次停用
            </button>
            <button className="px-3 py-1 text-sm text-red-600 hover:text-red-500">
              批次刪除
            </button>
          </div>
        </div>
      )}

      {/* 公司列表 */}
      {filteredCompanies.length === 0 ? (
        <div className="text-center py-12">
          <Building2 className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            沒有找到公司
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery || statusFilter !== "all"
              ? "嘗試調整搜尋條件或篩選器"
              : "開始建立您的第一家公司"}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {/* 表頭 */}
          <div className="flex items-center space-x-4 px-6 py-3 bg-gray-50 border rounded-lg text-sm font-medium text-gray-700">
            <input
              type="checkbox"
              checked={selectedCompanies.length === filteredCompanies.length}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="rounded border-gray-300"
            />
            <div className="flex-1 grid grid-cols-12 gap-4">
              <div className="col-span-4">公司名稱</div>
              <div className="col-span-2">狀態</div>
              <div className="col-span-2">聯絡資訊</div>
              <div className="col-span-2">用戶數</div>
              <div className="col-span-2">建立時間</div>
            </div>
            <div className="w-8">操作</div>
          </div>

          {/* 公司項目 */}
          {filteredCompanies.map((company) => (
            <CompanyItem
              key={company.id}
              company={company}
              isSelected={selectedCompanies.includes(String(company.id))}
              onSelect={() => handleCompanySelect(String(company.id))}
              onView={() => onCompanyView?.(company)}
              onEdit={() => onCompanyEdit?.(company)}
              onDelete={() => onCompanyDelete?.(company)}
              onActivate={() => onCompanyActivate?.(company)}
              onDeactivate={() => onCompanyDeactivate?.(company)}
              onUsers={() => onCompanyUsers?.(company)}
              onSettings={() => onCompanySettings?.(company)}
              formatDate={formatDate}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// 單個公司項目組件
interface CompanyItemProps {
  company: Company
  isSelected: boolean
  onSelect: () => void
  onView: () => void
  onEdit: () => void
  onDelete: () => void
  onActivate: () => void
  onDeactivate: () => void
  onUsers: () => void
  onSettings: () => void
  formatDate: (date: string) => string
}

function CompanyItem({
  company,
  isSelected,
  onSelect,
  onView,
  onEdit,
  onDelete,
  onActivate,
  onDeactivate,
  onUsers,
  onSettings,
  formatDate,
}: CompanyItemProps) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div
      className={cn(
        "flex items-center space-x-4 p-6 bg-white border rounded-lg hover:shadow-sm transition-shadow",
        isSelected && "ring-2 ring-blue-500 border-blue-500"
      )}>
      <input
        type="checkbox"
        checked={isSelected}
        onChange={onSelect}
        className="rounded border-gray-300"
      />

      <div className="flex-1 grid grid-cols-12 gap-4 items-center">
        {/* 公司名稱 */}
        <div className="col-span-4 flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            {company.logo_url ? (
              <Image
                src={company.logo_url}
                alt={company.name}
                width={32}
                height={32}
                className="w-8 h-8 rounded"
                style={{ objectFit: "cover" }}
              />
            ) : (
              <Building2 className="h-5 w-5 text-blue-600" />
            )}
          </div>
          <div className="min-w-0">
            <p className="font-medium text-gray-900 truncate">{company.name}</p>
            {company.description && (
              <p className="text-sm text-gray-500 truncate">
                {company.description}
              </p>
            )}
          </div>
        </div>

        {/* 狀態 */}
        <div className="col-span-2">
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
        </div>

        {/* 聯絡資訊 */}
        <div className="col-span-2 space-y-1">
          {company.email && (
            <div className="flex items-center text-sm text-gray-600">
              <Mail className="h-3 w-3 mr-1" />
              <span className="truncate">{company.email}</span>
            </div>
          )}
          {company.phone && (
            <div className="flex items-center text-sm text-gray-600">
              <Phone className="h-3 w-3 mr-1" />
              <span className="truncate">{company.phone}</span>
            </div>
          )}
          {company.website && (
            <div className="flex items-center text-sm text-gray-600">
              <Globe className="h-3 w-3 mr-1" />
              <span className="truncate">{company.website}</span>
            </div>
          )}
        </div>

        {/* 用戶數 */}
        <div className="col-span-2 text-sm text-gray-600">
          <div className="flex items-center">
            <Users className="h-4 w-4 mr-1" />
            {company.stats?.total_users || 0} 用戶
          </div>
        </div>

        {/* 建立時間 */}
        <div className="col-span-2 text-sm text-gray-600">
          <div className="flex items-center">
            <Calendar className="h-4 w-4 mr-1" />
            {formatDate(company.created_at)}
          </div>
        </div>
      </div>

      {/* 操作選單 */}
      <div className="relative">
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="p-1 text-gray-400 hover:text-gray-600">
          <MoreVertical className="h-4 w-4" />
        </button>

        {showMenu && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setShowMenu(false)}
            />
            <div className="absolute right-0 mt-1 w-48 bg-white border rounded-lg shadow-lg z-20">
              <button
                onClick={onView}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center">
                <Eye className="h-3 w-3 mr-2" />
                檢視詳情
              </button>
              <button
                onClick={onEdit}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center">
                <Edit className="h-3 w-3 mr-2" />
                編輯資訊
              </button>
              <button
                onClick={onUsers}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center">
                <Users className="h-3 w-3 mr-2" />
                管理用戶
              </button>
              <button
                onClick={onSettings}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center">
                <Settings className="h-3 w-3 mr-2" />
                公司設定
              </button>
              <div className="border-t border-gray-100">
                {company.is_active ? (
                  <button
                    onClick={onDeactivate}
                    className="w-full px-3 py-2 text-left text-sm text-orange-600 hover:bg-gray-50 flex items-center">
                    <PowerOff className="h-3 w-3 mr-2" />
                    停用公司
                  </button>
                ) : (
                  <button
                    onClick={onActivate}
                    className="w-full px-3 py-2 text-left text-sm text-green-600 hover:bg-gray-50 flex items-center">
                    <Power className="h-3 w-3 mr-2" />
                    啟用公司
                  </button>
                )}
                <button
                  onClick={onDelete}
                  className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-gray-50 flex items-center">
                  <Trash2 className="h-3 w-3 mr-2" />
                  刪除公司
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
