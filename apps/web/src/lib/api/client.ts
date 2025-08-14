/**
 * 通用 API 客戶端
 * 處理認證、錯誤處理、請求攔截等
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

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  /**
   * 通用請求方法
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = endpoint.startsWith('http')
      ? endpoint
      : `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`

    // 獲取認證 token
    const headers = await this.getHeaders(options.headers)

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

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

      // 如果是空回應（如 DELETE 操作）
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
   * GET 請求
   */
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

  /**
   * POST 請求
   */
  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * PUT 請求
   */
  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * DELETE 請求
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  /**
   * 獲取請求頭（包含認證信息）
   */
  private async getHeaders(customHeaders?: HeadersInit): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    // 添加自定義頭
    if (customHeaders) {
      if (customHeaders instanceof Headers) {
        customHeaders.forEach((value, key) => {
          headers[key] = value
        })
      } else if (Array.isArray(customHeaders)) {
        customHeaders.forEach(([key, value]) => {
          headers[key] = value
        })
      } else {
        Object.assign(headers, customHeaders)
      }
    }

    // 獲取並添加認證 token
    try {
      const session = await getSession()
      console.log('Session in API client:', session) // Debug log

      if (session?.user?.accessToken) {
        headers['Authorization'] = `Bearer ${session.user.accessToken}`
        console.log('Added Authorization header:', headers['Authorization'].substring(0, 20) + '...') // Debug log
      } else {
        console.warn('No accessToken found in session:', session?.user)
      }
    } catch (error) {
      console.warn('Failed to get session for API request:', error)
    }

    return headers
  }
}

// 創建默認實例
export const apiClient = new ApiClient()

// 統一 API 接口 - 按照後端實際路由結構組織
export const api = {
  // 基礎方法
  get: <T>(endpoint: string, params?: Record<string, unknown>) =>
    apiClient.get<T>(endpoint, params),

  post: <T>(endpoint: string, data?: unknown) =>
    apiClient.post<T>(endpoint, data),

  put: <T>(endpoint: string, data?: unknown) =>
    apiClient.put<T>(endpoint, data),

  delete: <T>(endpoint: string) =>
    apiClient.delete<T>(endpoint),

  // 系統用戶相關 API
  systemUsers: {
    // 登入
    login: (credentials: { email: string; password: string }) =>
      apiClient.post('/system-users/login', credentials),

    // 獲取用戶資料
    getProfile: () =>
      apiClient.get('/system-users/profile'),

    // 獲取用戶的公司列表
    getCompanies: () =>
      apiClient.get('/system-users/companies'),
  },

  // 管理員功能 API
  admin: {
    // 獲取所有公司
    getCompanies: () =>
      apiClient.get('/admin/companies'),

    // 獲取所有系統用戶
    getUsers: () =>
      apiClient.get('/admin/system-users'),
  },

  // 文檔管理 API
  documents: {
    // 上傳文檔
    upload: (formData: FormData) =>
      apiClient.request('/ingest/document', {
        method: 'POST',
        body: formData,
        headers: {}, // 讓瀏覽器自動設定 Content-Type for FormData
      }),

    // 獲取文檔狀態 (暫時使用 mock，等後端實作)
    getStatus: (taskId: string) =>
      Promise.resolve({ status: 'completed', progress: 100 }),

    // 獲取文檔列表 (暫時使用 mock，等後端實作)
    getList: (params?: any) =>
      Promise.resolve({ documents: [], total: 0, page: 1, limit: 20 }),
  },

  // 問答功能 API
  chat: {
    // 發送問題
    ask: (data: { question: string; company_id?: number }) =>
      apiClient.post('/ask', data),
  },

  // 健康檢查
  health: {
    check: () => apiClient.get('/health'),
  },
}