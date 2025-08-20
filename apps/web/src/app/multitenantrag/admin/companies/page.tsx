"use client"

import React, { useState, useEffect } from "react"
import {
  Plus,
  MessageSquare,
  FileText,
  BarChart3,
  Settings,
  Zap,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { companiesApi } from "@/lib/api/companiesApi"
import { Company } from "@/types/company"
import { useRouter } from "next/navigation"
import { CompanyCard } from "@/components/companies/CompanyCard"
import { 
  LineSettingsDialog,
  CompanyFormDialog,
  SystemConfigDialog,
  UserManagementDialog,
  DocumentManagementDialog
} from "@/components/companies"

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showLineDialog, setShowLineDialog] = useState(false)
  const [showSystemConfigDialog, setShowSystemConfigDialog] = useState(false)
  const [showUserManagementDialog, setShowUserManagementDialog] = useState(false)
  const [showDocumentDialog, setShowDocumentDialog] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null)
  const router = useRouter()

  useEffect(() => {
    loadCompanies()
  }, [])

  const loadCompanies = async () => {
    try {
      setLoading(true)
      const response = await companiesApi.getList({
        search: searchTerm || undefined,
      })
      
      // 為每個公司獲取統計數據
      const companiesWithStats = await Promise.all(
        response.companies.map(async (company) => {
          try {
            const stats = await companiesApi.getStats(company.id)
            return { ...company, stats }
          } catch (error) {
            console.error(`獲取公司 ${company.name} 統計失敗:`, error)
            return company
          }
        })
      )
      
      setCompanies(companiesWithStats)
    } catch (error) {
      console.error("載入公司列表失敗:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickSetup = (company: Company) => {
    setSelectedCompany(company)
    setShowLineDialog(true)
  }

  const handleLineSettings = (company: Company) => {
    setSelectedCompany(company)
    setShowLineDialog(true)
  }

  const handleEdit = (company: Company) => {
    setSelectedCompany(company)
    setShowEditDialog(true)
  }

  const handleToggleActive = async (company: Company) => {
    try {
      if (company.is_active) {
        await companiesApi.deactivate(company.id)
      } else {
        await companiesApi.activate(company.id)
      }
      await loadCompanies()
    } catch (error) {
      console.error("切換公司狀態失敗:", error)
    }
  }

  const handleSystemConfig = (company: Company) => {
    setSelectedCompany(company)
    setShowSystemConfigDialog(true)
  }

  const handleUserManagement = (company: Company) => {
    setSelectedCompany(company)
    setShowUserManagementDialog(true)
  }

  const handleDocuments = (company: Company) => {
    setSelectedCompany(company)
    setShowDocumentDialog(true)
  }

  const handleStats = (companyId: number) => {
    router.push(`/multitenantrag/admin/analytics?company=${companyId}`)
  }

  const filteredCompanies = companies.filter(
    (company) =>
      company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      company.code.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // 統計資料
  const totalCompanies = companies.length
  const activeCompanies = companies.filter(
    (c) => c.is_active && c.line_bot_enabled
  ).length
  const totalConversations = companies.reduce(
    (sum, company) => sum + (company.stats?.total_conversations || 0), 
    0
  )
  const totalDocuments = companies.reduce(
    (sum, company) => sum + (company.stats?.total_documents || 0), 
    0
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">載入中...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 統一管理後台標題 */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">
          🏢 多公司 AI 客服統一管理後台
        </h1>
        <p className="text-lg text-muted-foreground">
          設定各公司 LINE Channel 資料即可使用
        </p>
      </div>

      {/* 總覽儀表板 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總公司數</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCompanies} 家</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活躍公司</CardTitle>
            <Zap className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {activeCompanies} 家
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總對話數</CardTitle>
            <MessageSquare className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {totalConversations} 次
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總文檔數</CardTitle>
            <FileText className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{totalDocuments} 份</div>
          </CardContent>
        </Card>
      </div>

      {/* 快速操作 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-2xl font-bold">🚀 快速操作</h2>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新增公司
          </Button>
          <Button variant="outline">
            <BarChart3 className="mr-2 h-4 w-4" />
            系統監控
          </Button>
        </div>
        <div className="w-80">
          <Input
            placeholder="搜尋公司名稱或代碼..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* 公司卡片列表 */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">🏢 公司管理</h2>
        {filteredCompanies.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">沒有找到公司</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm ? "請嘗試其他搜尋關鍵字" : "開始新增第一家公司"}
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="mr-2 h-4 w-4" />
                新增公司
              </Button>
            </CardContent>
          </Card>
        ) : (
          filteredCompanies.map((company) => (
            <CompanyCard
              key={company.id}
              company={company}
              onQuickSetup={handleQuickSetup}
              onLineSettings={handleLineSettings}
              onEdit={handleEdit}
              onToggleActive={handleToggleActive}
              onSystemConfig={handleSystemConfig}
              onUserManagement={handleUserManagement}
              onDocuments={handleDocuments}
              onStats={handleStats}
              onRefresh={loadCompanies}
            />
          ))
        )}
      </div>

      {/* 對話框 */}
      <CompanyFormDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={loadCompanies}
      />

      <CompanyFormDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        company={selectedCompany}
        onSuccess={loadCompanies}
      />

      <LineSettingsDialog
        open={showLineDialog}
        onOpenChange={setShowLineDialog}
        company={selectedCompany}
        onSuccess={loadCompanies}
      />

      <SystemConfigDialog
        open={showSystemConfigDialog}
        onOpenChange={setShowSystemConfigDialog}
        company={selectedCompany}
        onSuccess={loadCompanies}
      />

      <UserManagementDialog
        open={showUserManagementDialog}
        onOpenChange={setShowUserManagementDialog}
        company={selectedCompany}
        onSuccess={loadCompanies}
      />

      <DocumentManagementDialog
        open={showDocumentDialog}
        onOpenChange={setShowDocumentDialog}
        company={selectedCompany}
      />
    </div>
  )
}
