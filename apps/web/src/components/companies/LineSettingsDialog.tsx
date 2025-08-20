"use client"

import React, { useState, useEffect } from "react"
import {
  MessageSquare,
  CheckCircle,
  AlertTriangle,
  Eye,
  EyeOff,
  TestTube,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Company } from "@/types/company"
import { companiesApi } from "@/lib/api/companiesApi"

interface LineSettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  company: Company | null
  onSuccess: () => void
}

export function LineSettingsDialog({
  open,
  onOpenChange,
  company,
  onSuccess,
}: LineSettingsDialogProps) {
  const [channelToken, setChannelToken] = useState("")
  const [channelSecret, setChannelSecret] = useState("")
  const [botEnabled, setBotEnabled] = useState(true)
  const [showToken, setShowToken] = useState(false)
  const [showSecret, setShowSecret] = useState(false)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    if (company && open) {
      setChannelToken(company.line_channel_token || "")
      setChannelSecret(company.line_channel_secret || "")
      setBotEnabled(company.line_bot_enabled || false)
    }
  }, [company, open])

  const handleSave = async () => {
    if (!company) return

    try {
      setLoading(true)

      // 使用新的 LINE 設定 API
      await companiesApi.updateLineSettings(company.id, {
        line_channel_token: channelToken,
        line_channel_secret: channelSecret,
        line_bot_enabled: botEnabled,
      })

      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error("更新 LINE 設定失敗:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    if (!company || !channelToken || !channelSecret) return

    try {
      setTesting(true)

      // 先保存設定再測試
      await companiesApi.updateLineSettings(company.id, {
        line_channel_token: channelToken,
        line_channel_secret: channelSecret,
        line_bot_enabled: botEnabled,
      })

      // 測試 LINE 連接
      const result = await companiesApi.testLineConnection(company.id)

      if (result.success) {
        alert(`LINE Bot 連接測試成功！\n${result.message}`)
      } else {
        alert(`LINE Bot 連接測試失敗：\n${result.message}`)
      }
    } catch (error) {
      console.error("LINE Bot 測試失敗:", error)
      alert("LINE Bot 連接測試失敗，請檢查設定")
    } finally {
      setTesting(false)
    }
  }

  if (!company) return null

  const isConfigured = channelToken && channelSecret
  const isCurrentlyEnabled =
    company.line_bot_enabled && company.line_channel_token

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>💬 LINE Bot 設定</span>
          </DialogTitle>
          <DialogDescription>
            為 <strong>{company.name}</strong> 設定 LINE Channel 資料即可啟用 AI
            客服
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 目前狀態 */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center space-x-3">
              {isCurrentlyEnabled ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="font-medium">LINE Bot 已啟用</p>
                    <p className="text-sm text-muted-foreground">
                      AI 客服正在運行中
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  <div>
                    <p className="font-medium">LINE Bot 未設定</p>
                    <p className="text-sm text-muted-foreground">
                      需要設定 Channel 資料
                    </p>
                  </div>
                </>
              )}
            </div>
            <Badge variant={isCurrentlyEnabled ? "default" : "secondary"}>
              {isCurrentlyEnabled ? "運行中" : "未啟用"}
            </Badge>
          </div>

          {/* LINE Channel Token */}
          <div className="space-y-2">
            <Label htmlFor="channelToken">LINE Channel Access Token *</Label>
            <div className="relative">
              <Input
                id="channelToken"
                type={showToken ? "text" : "password"}
                placeholder="請輸入 LINE Channel Access Token"
                value={channelToken}
                onChange={(e) => setChannelToken(e.target.value)}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowToken(!showToken)}>
                {showToken ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              從 LINE Developers Console 取得的 Channel Access Token
            </p>
          </div>

          {/* LINE Channel Secret */}
          <div className="space-y-2">
            <Label htmlFor="channelSecret">LINE Channel Secret *</Label>
            <div className="relative">
              <Input
                id="channelSecret"
                type={showSecret ? "text" : "password"}
                placeholder="請輸入 LINE Channel Secret"
                value={channelSecret}
                onChange={(e) => setChannelSecret(e.target.value)}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowSecret(!showSecret)}>
                {showSecret ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              從 LINE Developers Console 取得的 Channel Secret
            </p>
          </div>

          {/* 啟用開關 */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-1">
              <Label htmlFor="botEnabled">啟用 LINE Bot</Label>
              <p className="text-sm text-muted-foreground">
                開啟後用戶可以透過 LINE 與 AI 客服對話
              </p>
            </div>
            <Switch
              id="botEnabled"
              checked={botEnabled}
              onCheckedChange={setBotEnabled}
            />
          </div>

          {/* 測試按鈕 */}
          {isConfigured && (
            <div className="flex justify-center">
              <Button variant="outline" onClick={handleTest} disabled={testing}>
                <TestTube className="mr-2 h-4 w-4" />
                {testing ? "測試中..." : "🧪 測試連接"}
              </Button>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={handleSave}
            disabled={loading || !channelToken || !channelSecret}>
            {loading ? "儲存中..." : "💾 儲存設定"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
