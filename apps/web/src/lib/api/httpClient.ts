/**
 * 核心 HTTP 客戶端
 * 處理所有網路請求、認證、錯誤處理
 */

import { getSession } from 'next-auth/react'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: Response
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

class HttpClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  /**
   * 核心請求方法
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
    
    // 獲取認證頭
    const headers = await this.getAuthHeaders(options.headers)

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      // 處理 401 錯誤 - token 過期
      if (response.status === 401) {
        this.handleUnauthorized()
        throw new ApiError('Unauthorized', 401, response)
      }

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = errorText

        try {
          const errorJson = JSON.parse(errorText)
          errorMessage = errorJson.detail || errorJson.message || errorText
        } catch {
          // 如果不是 JSON，使用原始文本
        }

        throw new ApiError(
          errorMessage || `Request failed with status ${response.status}`,
          response.status,
          response
        )
      }

      // 處理空響應
      const contentType = response.headers.get('content-type')
      if (!contentType?.includes('application/json')) {
        return {} as T
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }

      throw new ApiError(
        error instanceof Error ? error.message : 'Network error',
        0
      )
    }
  }

  /**
   * 獲取認證頭
   */
  private async getAuthHeaders(customHeaders?: HeadersInit): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // 添加自定義頭
    if (customHeaders) {
      Object.assign(headers, customHeaders)
    }

    // 獲取 JWT token
    try {
      const session = await getSession()
      if (session?.user?.accessToken) {
        headers['Authorization'] = `Bearer ${session.user.accessToken}`
      }
    } catch (error) {
      console.warn('Failed to get session for API request:', error)
    }

    return headers
  }

  /**
   * 處理 401 未授權錯誤
   */
  private handleUnauthorized() {
    if (typeof window === 'undefined') return

    const currentPath = window.location.pathname
    
    if (!currentPath.includes('/auth/login')) {
      // 保存當前路徑用於登入後重定向
      sessionStorage.setItem('redirectAfterLogin', currentPath)
      
      // 使用動態導入避免服務端執行
      import('next-auth/react').then(async ({ signOut }) => {
        try {
          await signOut({ redirect: false })
          window.location.href = '/multitenantrag/auth/login?reason=session_expired'
        } catch (error) {
          console.error('Logout failed:', error)
          window.location.href = '/multitenantrag/auth/login?reason=session_expired'
        }
      }).catch(() => {
        window.location.href = '/multitenantrag/auth/login?reason=session_expired'
      })
    }
  }

  // ==================== 公共方法 ====================

  async get<T>(endpoint: string, params?: Record<string, unknown>): Promise<T> {
    let url = endpoint

    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })

      const queryString = searchParams.toString()
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString
      }
    }

    return this.request<T>(url, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const options: RequestInit = {
      method: 'POST',
    }

    if (data instanceof FormData) {
      // FormData 不需要設定 Content-Type
      options.body = data
      options.headers = {} // 讓瀏覽器自動設定
    } else if (data) {
      options.body = JSON.stringify(data)
    }

    return this.request<T>(endpoint, options)
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

// 創建全局實例
export const httpClient = new HttpClient()

// 為了簡化使用，導出快捷方法
export const api = {
  get: <T>(endpoint: string, params?: Record<string, unknown>) =>
    httpClient.get<T>(endpoint, params),
  post: <T>(endpoint: string, data?: unknown) =>
    httpClient.post<T>(endpoint, data),
  put: <T>(endpoint: string, data?: unknown) =>
    httpClient.put<T>(endpoint, data),
  delete: <T>(endpoint: string) =>
    httpClient.delete<T>(endpoint),
}