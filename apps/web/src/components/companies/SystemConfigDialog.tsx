"use client"

import React, { useState, useEffect } from "react"
import { Settings, Save } from "lucide-react"
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
import { companiesApi } from "@/lib/api/companiesApi"
import { Company } from "@/types/company"

interface SystemConfigDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  company: Company | null
  onSuccess: () => void
}

export function SystemConfigDialog({
  open,
  onOpenChange,
  company,
  onSuccess,
}: SystemConfigDialogProps) {
  const [configData, setConfigData] = useState({
    max_documents: 0,
    max_queries_per_month: 0,
    storage_quota_gb: 0,
    rag_working_dir: "",
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (company && open) {
      setConfigData({
        max_documents: company.max_documents || 0,
        max_queries_per_month: company.max_queries_per_month || 0,
        storage_quota_gb: company.storage_quota_gb || 0,
        rag_working_dir: company.rag_working_dir || "",
      })
    }
  }, [company, open])

  const handleSave = async () => {
    if (!company) return

    try {
      setLoading(true)

      // 使用現有的更新 API，傳入系統配置
      await companiesApi.update(company.id, {
        max_documents: configData.max_documents,
        max_queries_per_month: configData.max_queries_per_month,
        storage_quota_gb: configData.storage_quota_gb,
        rag_working_dir: configData.rag_working_dir,
      })

      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error("更新系統配置失敗:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    if (field === "rag_working_dir") {
      setConfigData((prev) => ({
        ...prev,
        [field]: value,
      }))
    } else {
      const numValue = parseInt(value) || 0
      setConfigData((prev) => ({
        ...prev,
        [field]: numValue,
      }))
    }
  }

  if (!company) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>⚙️ 系統配置管理</span>
          </DialogTitle>
          <DialogDescription>
            設定 <strong>{company.name}</strong> 的系統配額和限制
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 overflow-y-auto flex-1 px-1">
          {/* 文檔數量限制 */}
          <div className="space-y-2">
            <Label htmlFor="max_documents">文檔數量限制</Label>
            <Input
              id="max_documents"
              type="number"
              min="0"
              placeholder="1000"
              value={configData.max_documents}
              onChange={(e) =>
                handleInputChange("max_documents", e.target.value)
              }
            />
            <p className="text-xs text-muted-foreground">
              設定 0 表示無限制。當前已上傳：
              {company.stats?.total_documents || 0} 份文檔
            </p>
          </div>

          {/* 每月查詢次數限制 */}
          <div className="space-y-2">
            <Label htmlFor="max_queries_per_month">每月查詢次數限制</Label>
            <Input
              id="max_queries_per_month"
              type="number"
              min="0"
              placeholder="10000"
              value={configData.max_queries_per_month}
              onChange={(e) =>
                handleInputChange("max_queries_per_month", e.target.value)
              }
            />
            <p className="text-xs text-muted-foreground">
              設定 0 表示無限制。本月已查詢：
              {company.stats?.monthly_conversations || 0} 次
            </p>
          </div>

          {/* 儲存空間配額 */}
          <div className="space-y-2">
            <Label htmlFor="storage_quota_gb">儲存空間配額 (GB)</Label>
            <Input
              id="storage_quota_gb"
              type="number"
              min="0"
              placeholder="100"
              value={configData.storage_quota_gb}
              onChange={(e) =>
                handleInputChange("storage_quota_gb", e.target.value)
              }
            />
            <p className="text-xs text-muted-foreground">
              設定 0 表示無限制。當前已使用：
              {company.stats?.storage_used
                ? `${(
                    company.stats.storage_used /
                    (1024 * 1024 * 1024)
                  ).toFixed(2)} GB`
                : "0 GB"}
            </p>
          </div>

          {/* RAG 工作目錄 */}
          <div className="space-y-2">
            <Label htmlFor="rag_working_dir">RAG 工作目錄</Label>
            <Input
              id="rag_working_dir"
              placeholder="./rag_storage/company_1"
              value={configData.rag_working_dir}
              onChange={(e) =>
                handleInputChange("rag_working_dir", e.target.value)
              }
            />
            <p className="text-xs text-muted-foreground">
              設定該公司的 RAG 處理工作目錄，留空使用預設路徑
            </p>
          </div>

          {/* 配額狀態提示 */}
          <div className="p-4 bg-muted/50 rounded-lg">
            <h4 className="font-medium mb-2">💡 配額說明</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 設定為 0 表示無限制使用</li>
              <li>• 超過限制時系統會自動提醒用戶</li>
              <li>• 管理員可隨時調整這些配額</li>
              <li>• 變更會立即生效</li>
            </ul>
          </div>
        </div>

        <DialogFooter className="flex-shrink-0 border-t pt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            <Save className="mr-2 h-4 w-4" />
            {loading ? "儲存中..." : "💾 儲存配置"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
