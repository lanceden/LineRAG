"use client"

import React from "react"
import {
  MessageSquare,
  FileText,
  BarChart3,
  Settings,
  Zap,
  AlertTriangle,
  CheckCircle,
  Calendar,
  Edit,
  Power,
  PowerOff,
  Users,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Company, CompanyStats } from "@/types/company"

interface CompanyCardProps {
  company: Company & { stats?: CompanyStats }
  onQuickSetup: (company: Company) => void
  onLineSettings: (company: Company) => void
  onDocuments: (company: Company) => void
  onStats: (companyId: number) => void
  onEdit: (company: Company) => void
  onToggleActive: (company: Company) => void
  onSystemConfig: (company: Company) => void
  onUserManagement: (company: Company) => void
  onRefresh: () => void
}

export function CompanyCard({
  company,
  onQuickSetup,
  onLineSettings,
  onDocuments,
  onStats,
  onEdit,
  onToggleActive,
  onSystemConfig,
  onUserManagement,
}: CompanyCardProps) {
  const isLineBotEnabled =
    company.line_bot_enabled && company.line_channel_token
  const documentCount = company.stats?.total_documents || 0
  const todayConversations = company.stats?.total_conversations || 0

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          {/* 左側：公司資訊 */}
          <div className="flex items-start space-x-4">
            {/* 公司圖標 */}
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
              {company.name.charAt(0)}
            </div>

            {/* 公司詳情 */}
            <div className="space-y-2">
              <div>
                <h3 className="text-xl font-bold">{company.name}</h3>
                <p className="text-sm text-muted-foreground">
                  代碼: {company.code}
                </p>
              </div>

              {/* 狀態指標 */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  {isLineBotEnabled ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <Badge
                        variant="default"
                        className="bg-green-100 text-green-800">
                        💬 LINE Bot 已啟用
                      </Badge>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <Badge
                        variant="secondary"
                        className="bg-orange-100 text-orange-800">
                        ❌ LINE Bot 未設定
                      </Badge>
                    </>
                  )}
                </div>

                <Badge variant={company.is_active ? "default" : "secondary"}>
                  {company.is_active ? "啟用中" : "已停用"}
                </Badge>
              </div>

              {/* 統計資訊 */}
              <div className="flex items-center space-x-6 text-sm text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <FileText className="h-4 w-4" />
                  <span>{documentCount} 份文檔</span>
                </div>
                <div className="flex items-center space-x-1">
                  <MessageSquare className="h-4 w-4" />
                  <span>總對話: {todayConversations} 次</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span>
                    建立於{" "}
                    {new Date(company.created_at).toLocaleDateString("zh-TW")}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 右側：操作按鈕 */}
          <div className="flex flex-col space-y-2">
            {!isLineBotEnabled ? (
              <Button
                onClick={() => onQuickSetup(company)}
                disabled={!company.is_active}
                className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 disabled:opacity-50">
                <Zap className="mr-2 h-4 w-4" />
                🚀 快速設定
              </Button>
            ) : (
              <Button
                onClick={() => onLineSettings(company)}
                variant="outline"
                disabled={!company.is_active}>
                <Settings className="mr-2 h-4 w-4" />
                ⚙️ LINE設定
              </Button>
            )}

            {/* 啟用/停用按鈕 */}
            <Button
              onClick={() => onToggleActive(company)}
              variant={company.is_active ? "destructive" : "default"}
              className={
                company.is_active
                  ? ""
                  : "bg-green-600 hover:bg-green-700 text-white"
              }>
              {company.is_active ? (
                <>
                  <PowerOff className="mr-2 h-4 w-4" />
                  🔴 停用公司
                </>
              ) : (
                <>
                  <Power className="mr-2 h-4 w-4" />
                  🟢 啟用公司
                </>
              )}
            </Button>

            <div className="grid grid-cols-2 gap-1">
              <Button
                size="sm"
                variant="outline"
                disabled={!company.is_active}
                onClick={() => onEdit(company)}>
                <Edit className="mr-1 h-3 w-3" />
                ✏️ 編輯
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!company.is_active}
                onClick={() => onSystemConfig(company)}>
                <Settings className="mr-1 h-3 w-3" />
                ⚙️ 配置
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!company.is_active}
                onClick={() => onUserManagement(company)}>
                <Users className="mr-1 h-3 w-3" />
                👥 用戶
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!company.is_active}
                onClick={() => onDocuments(company)}>
                <FileText className="mr-1 h-3 w-3" />
                📄 文檔
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!company.is_active}
                onClick={() => onStats(company.id)}>
                <BarChart3 className="mr-1 h-3 w-3" />
                📈 統計
              </Button>
            </div>
          </div>
        </div>

        {/* 底部：快速資訊 */}
        {isLineBotEnabled && (
          <div className="mt-4 pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-4">
                <span className="text-muted-foreground">LINE Channel:</span>
                <code className="bg-muted px-2 py-1 rounded text-xs">
                  {company.line_channel_token?.substring(0, 20)}...
                </code>
              </div>
              <div className="flex items-center space-x-2 text-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>運行中</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
