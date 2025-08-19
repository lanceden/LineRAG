"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Copy,
  TestTube,
  CheckCircle,
  XCircle,
  AlertCircle,
  ExternalLink,
} from "lucide-react"
import { toast } from "sonner"
import type {
  Company,
  LineSettingsUpdateRequest,
  LineConnectionTestResult,
} from "@/types/company"
import { companiesApi } from "@/lib/api/companiesApi"

interface LineSettingsProps {
  company: Company
  onUpdate: (company: Company) => void
}

export function LineSettings({ company, onUpdate }: LineSettingsProps) {
  const [settings, setSettings] = useState<LineSettingsUpdateRequest>({
    line_channel_token: company.line_channel_token || "",
    line_channel_secret: company.line_channel_secret || "",
    line_bot_enabled: company.line_bot_enabled || false,
  })

  const [isLoading, setIsLoading] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<LineConnectionTestResult | null>(
    null
  )
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // 生成 Webhook URL
  const webhookUrl = companiesApi.getWebhookUrl(company.code)

  // 處理設定變更
  const handleSettingChange = (
    field: keyof LineSettingsUpdateRequest,
    value: string | boolean
  ) => {
    setSettings((prev) => ({ ...prev, [field]: value }))
    setHasUnsavedChanges(true)
    setTestResult(null) // 清除測試結果
  }

  // 儲存設定
  const handleSave = async () => {
    setIsLoading(true)
    try {
      const updatedCompany = await companiesApi.updateLineSettings(
        company.id,
        settings
      )
      onUpdate(updatedCompany)
      setHasUnsavedChanges(false)
      toast.success("LINE 設定已更新")
    } catch (error) {
      console.error("更新 LINE 設定失敗:", error)
      toast.error("更新失敗，請稍後再試")
    } finally {
      setIsLoading(false)
    }
  }

  // 測試連線
  const handleTestConnection = async () => {
    if (!settings.line_channel_token || !settings.line_channel_secret) {
      toast.error("請先填入 Channel Token 和 Channel Secret")
      return
    }

    setIsTesting(true)
    try {
      const result = await companiesApi.testLineConnection(company.id)
      setTestResult(result)

      if (result.success) {
        toast.success("LINE 連線測試成功")
      } else {
        toast.error(`連線測試失敗: ${result.message}`)
      }
    } catch (error) {
      console.error("測試連線失敗:", error)
      setTestResult({
        success: false,
        message: "測試連線時發生錯誤，請稍後再試",
      })
      toast.error("測試連線失敗")
    } finally {
      setIsTesting(false)
    }
  }

  // 複製到剪貼簿
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success("已複製到剪貼簿")
    } catch (error) {
      console.error("複製失敗:", error)
      toast.error("複製失敗")
    }
  }

  return (
    <div className="space-y-6">
      {/* 基本設定 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">L</span>
            </div>
            LINE Bot 設定
          </CardTitle>
          <CardDescription>
            設定您的 LINE Channel 資訊以啟用 LINE Bot 功能
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 啟用開關 */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="line-enabled">啟用 LINE Bot</Label>
              <p className="text-sm text-muted-foreground">
                開啟後用戶可以透過 LINE 與 AI 客服對話
              </p>
            </div>
            <Switch
              id="line-enabled"
              checked={settings.line_bot_enabled}
              onCheckedChange={(checked) =>
                handleSettingChange("line_bot_enabled", checked)
              }
            />
          </div>

          {/* Channel Token */}
          <div className="space-y-2">
            <Label htmlFor="channel-token">Channel Access Token</Label>
            <Input
              id="channel-token"
              type="password"
              placeholder="請輸入 LINE Channel Access Token"
              value={settings.line_channel_token}
              onChange={(e) =>
                handleSettingChange("line_channel_token", e.target.value)
              }
              disabled={!settings.line_bot_enabled}
            />
            <p className="text-sm text-muted-foreground">
              從 LINE Developers Console 取得的 Channel Access Token
            </p>
          </div>

          {/* Channel Secret */}
          <div className="space-y-2">
            <Label htmlFor="channel-secret">Channel Secret</Label>
            <Input
              id="channel-secret"
              type="password"
              placeholder="請輸入 LINE Channel Secret"
              value={settings.line_channel_secret}
              onChange={(e) =>
                handleSettingChange("line_channel_secret", e.target.value)
              }
              disabled={!settings.line_bot_enabled}
            />
            <p className="text-sm text-muted-foreground">
              用於驗證來自 LINE 的請求
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Webhook 設定 */}
      <Card>
        <CardHeader>
          <CardTitle>Webhook 設定</CardTitle>
          <CardDescription>
            將此 Webhook URL 設定到您的 LINE Developers Console
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Webhook URL</Label>
            <div className="flex gap-2">
              <Input
                value={webhookUrl}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => copyToClipboard(webhookUrl)}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              請在 LINE Developers Console 的 Messaging API 設定中，將此 URL
              設定為 Webhook URL
            </p>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              設定完成後，請記得在 LINE Developers Console 中啟用 &quot;Use
              webhook&quot; 選項
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* 測試結果 */}
      {testResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {testResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              連線測試結果
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert
              className={
                testResult.success
                  ? "border-green-200 bg-green-50"
                  : "border-red-200 bg-red-50"
              }>
              <AlertDescription
                className={
                  testResult.success ? "text-green-800" : "text-red-800"
                }>
                {testResult.message}
              </AlertDescription>
            </Alert>

            {testResult.success && testResult.channel_info && (
              <div className="mt-4 space-y-2">
                <h4 className="font-medium">Channel 資訊</h4>
                <div className="text-sm space-y-1">
                  <p>
                    <strong>Channel ID:</strong>{" "}
                    {testResult.channel_info.channel_id}
                  </p>
                  <p>
                    <strong>Channel 名稱:</strong>{" "}
                    {testResult.channel_info.channel_name}
                  </p>
                  {testResult.channel_info.channel_description && (
                    <p>
                      <strong>描述:</strong>{" "}
                      {testResult.channel_info.channel_description}
                    </p>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 操作按鈕 */}
      <div className="flex gap-3">
        <Button
          onClick={handleSave}
          disabled={isLoading || !hasUnsavedChanges}
          className="flex-1">
          {isLoading ? "儲存中..." : "儲存設定"}
        </Button>

        <Button
          variant="outline"
          onClick={handleTestConnection}
          disabled={
            isTesting ||
            !settings.line_channel_token ||
            !settings.line_channel_secret
          }
          className="flex items-center gap-2">
          <TestTube className="h-4 w-4" />
          {isTesting ? "測試中..." : "測試連線"}
        </Button>

        <Button variant="outline" asChild>
          <a
            href="https://developers.line.biz/console/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4" />
            LINE Console
          </a>
        </Button>
      </div>

      {/* 說明文件 */}
      <Card>
        <CardHeader>
          <CardTitle>設定說明</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="text-sm space-y-2">
            <h4 className="font-medium">如何取得 LINE Channel 資訊：</h4>
            <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
              <li>
                前往{" "}
                <a
                  href="https://developers.line.biz/console/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline">
                  LINE Developers Console
                </a>
              </li>
              <li>選擇您的 Provider 和 Channel</li>
              <li>
                在 &quot;Messaging API&quot; 標籤中找到 Channel Access Token
              </li>
              <li>在 &quot;Basic settings&quot; 標籤中找到 Channel Secret</li>
              <li>
                將上方的 Webhook URL 設定到 &quot;Messaging API&quot; 的 Webhook
                URL 欄位
              </li>
              <li>啟用 &quot;Use webhook&quot; 選項</li>
            </ol>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
