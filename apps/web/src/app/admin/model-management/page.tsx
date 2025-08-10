"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Loader2,
  RefreshCw,
} from "lucide-react"

interface ModelInfo {
  id: string
  name: string
  displayName: string
  description: string
  vramUsage: string
  capabilities: string[]
}

interface ModelStatus {
  currentModel: string
  status: "running" | "error" | "stopped"
  lastCheckTime?: string
  modelInfo?: ModelInfo
}

export default function ModelManagementPage() {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refreshStatus = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const apiUrl =
        process.env.NEXT_PUBLIC_PYTHON_API_URL || "http://localhost:8000"
      const response = await fetch(`${apiUrl}/admin/model/status`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setModelStatus(data)
    } catch (err) {
      console.error("Failed to fetch model status:", err)
      setError("無法獲取模型狀態")
    } finally {
      setIsLoading(false)
    }
  }

  const getCurrentModelInfo = () => {
    return modelStatus?.modelInfo
  }

  const getStatusBadge = () => {
    switch (modelStatus?.status) {
      case "running":
        return (
          <Badge className="bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            運行中
          </Badge>
        )
      case "error":
        return (
          <Badge className="bg-red-100 text-red-800">
            <AlertTriangle className="w-3 h-3 mr-1" />
            錯誤
          </Badge>
        )
      case "stopped":
        return (
          <Badge className="bg-gray-100 text-gray-800">
            <Clock className="w-3 h-3 mr-1" />
            已停止
          </Badge>
        )
      default:
        return <Badge className="bg-gray-100 text-gray-800">未知</Badge>
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">AI模型管理</h1>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refreshStatus}
            disabled={isLoading}>
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            重新整理
          </Button>
          {getStatusBadge()}
        </div>
      </div>

      {/* 錯誤顯示 */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* 當前模型狀態 */}
      <Card>
        <CardHeader>
          <CardTitle>當前使用模型</CardTitle>
        </CardHeader>
        <CardContent>
          {getCurrentModelInfo() ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold">
                    {getCurrentModelInfo()?.displayName}
                  </h3>
                  <p className="text-gray-600">
                    {getCurrentModelInfo()?.description}
                  </p>
                  <div className="flex space-x-2 mt-2">
                    {getCurrentModelInfo()?.capabilities.map((cap: string) => (
                      <Badge key={cap} variant="outline">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">記憶體使用</p>
                  <p className="font-mono">
                    {getCurrentModelInfo()?.vramUsage}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">無法獲取模型資訊</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 系統監控與操作 */}
      <Card>
        <CardHeader>
          <CardTitle>系統監控與維護</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                本系統採用穩定的固定模型配置，確保服務品質一致性。如需調整模型配置或遇到技術問題，請聯繫技術支援團隊。
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <label className="text-sm font-medium text-gray-600">
                  推理服務狀態
                </label>
                <p className="text-lg font-semibold mt-1">
                  {modelStatus?.status === "running" ? (
                    <span className="text-green-600 flex items-center">
                      <CheckCircle className="w-5 h-5 mr-1" />
                      正常運行
                    </span>
                  ) : (
                    <span className="text-red-600 flex items-center">
                      <AlertTriangle className="w-5 h-5 mr-1" />
                      服務異常
                    </span>
                  )}
                </p>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <label className="text-sm font-medium text-gray-600">
                  模型端點
                </label>
                <p className="text-sm text-gray-700 mt-1 font-mono">
                  localhost:8001/v1
                </p>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <label className="text-sm font-medium text-gray-600">
                  最後檢查時間
                </label>
                <p className="text-sm text-gray-700 mt-1">
                  {modelStatus?.lastCheckTime
                    ? new Date(modelStatus.lastCheckTime).toLocaleString(
                        "zh-TW",
                        {
                          year: "numeric",
                          month: "2-digit",
                          day: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        }
                      )
                    : "未知"}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t">
              <h4 className="font-medium mb-2">技術支援聯絡方式</h4>
              <p className="text-sm text-gray-600 mb-2">
                如遇到模型服務異常或需要技術協助，請通過以下方式聯繫：
              </p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 工作時間支援：週一至週五 9:00-18:00</li>
                <li>• 緊急技術熱線：提供7x24小時支援</li>
                <li>• 系統監控：自動異常檢測與通知</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
