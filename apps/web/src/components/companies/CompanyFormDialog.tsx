"use client"

import React, { useState, useEffect } from "react"
import { Plus, Building2, Edit } from "lucide-react"
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
import { Textarea } from "../ui/textarea"
import { Company } from "@/types/company"

interface CompanyFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
  company?: Company | null // 如果有公司資料則為編輯模式
}

export function CompanyFormDialog({
  open,
  onOpenChange,
  onSuccess,
  company,
}: CompanyFormDialogProps) {
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    description: "",
    contact_email: "",
    contact_phone: "",
  })
  const [loading, setLoading] = useState(false)
  const isEditMode = !!company

  // 當對話框開啟時，如果是編輯模式則填入現有資料
  useEffect(() => {
    if (open && company) {
      setFormData({
        name: company.name || "",
        code: company.code || "",
        description: company.description || "",
        contact_email: company.email || "",
        contact_phone: company.phone || "",
      })
    } else if (open && !company) {
      // 新增模式時重置表單
      setFormData({
        name: "",
        code: "",
        description: "",
        contact_email: "",
        contact_phone: "",
      })
    }
  }, [open, company])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      setLoading(true)
      
      // 映射前端欄位名稱到後端期望的名稱
      const submitData = {
        name: formData.name,
        code: formData.code,
        description: formData.description,
        email: formData.contact_email,
        phone: formData.contact_phone,
      }
      
      if (isEditMode && company) {
        // 編輯模式
        await companiesApi.update(company.id, submitData)
      } else {
        // 新增模式
        await companiesApi.create(submitData)
      }

      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error(isEditMode ? "更新公司失敗:" : "創建公司失敗:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            {isEditMode ? (
              <>
                <Edit className="h-5 w-5" />
                <span>✏️ 編輯公司資訊</span>
              </>
            ) : (
              <>
                <Building2 className="h-5 w-5" />
                <span>🏢 新增公司</span>
              </>
            )}
          </DialogTitle>
          <DialogDescription>
            {isEditMode 
              ? `修改 ${company?.name} 的基本資訊`
              : "新增公司到統一管理後台，設定完成後即可啟用 AI 客服"
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 公司名稱 */}
          <div className="space-y-2">
            <Label htmlFor="name">公司名稱 *</Label>
            <Input
              id="name"
              placeholder="例如：示範公司 A"
              value={formData.name}
              onChange={(e) => handleInputChange("name", e.target.value)}
              required
            />
          </div>

          {/* 公司代碼 */}
          <div className="space-y-2">
            <Label htmlFor="code">公司代碼 *</Label>
            <Input
              id="code"
              placeholder="例如：DEMO_A"
              value={formData.code}
              onChange={(e) =>
                handleInputChange("code", e.target.value.toUpperCase())
              }
              disabled={isEditMode}
              required
            />
            <p className="text-xs text-muted-foreground">
              {isEditMode 
                ? "公司代碼建立後無法修改"
                : "用於系統識別，建議使用英文大寫和底線"
              }
            </p>
          </div>

          {/* 公司描述 */}
          <div className="space-y-2">
            <Label htmlFor="description">公司描述</Label>
            <Textarea
              id="description"
              placeholder="簡單描述這家公司的業務..."
              value={formData.description}
              onChange={(e) => handleInputChange("description", e.target.value)}
              rows={3}
            />
          </div>

          {/* 聯絡資訊 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="contact_email">聯絡信箱</Label>
              <Input
                id="contact_email"
                type="email"
                placeholder="contact@company.com"
                value={formData.contact_email}
                onChange={(e) =>
                  handleInputChange("contact_email", e.target.value)
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="contact_phone">聯絡電話</Label>
              <Input
                id="contact_phone"
                placeholder="02-1234-5678"
                value={formData.contact_phone}
                onChange={(e) =>
                  handleInputChange("contact_phone", e.target.value)
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button
              type="submit"
              disabled={loading || !formData.name || !formData.code}>
              {isEditMode ? (
                <>
                  <Edit className="mr-2 h-4 w-4" />
                  {loading ? "更新中..." : "💾 儲存變更"}
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  {loading ? "創建中..." : "🏢 創建公司"}
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
