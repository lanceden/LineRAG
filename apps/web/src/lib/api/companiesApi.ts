/**
 * 公司管理 API
 */

import { httpClient } from './httpClient'
import type {
  Company,
  CompanyListResponse,
  CompanyStats,
  CreateCompanyRequest,
  UpdateCompanyRequest,
} from '@/types/company'

export const companiesApi = {
  /**
   * 獲取公司列表
   */
  getList: (params?: {
    page?: number
    limit?: number
    search?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  }): Promise<CompanyListResponse> =>
    httpClient.get('/api/companies', params),

  /**
   * 獲取單個公司
   */
  getById: (id: number): Promise<Company> =>
    httpClient.get(`/api/companies/${id}`),

  /**
   * 創建公司
   */
  create: (data: CreateCompanyRequest): Promise<Company> =>
    httpClient.post('/api/companies', data),

  /**
   * 更新公司
   */
  update: (id: number, data: UpdateCompanyRequest): Promise<Company> =>
    httpClient.put(`/api/companies/${id}`, data),

  /**
   * 刪除公司
   */
  delete: (id: number): Promise<{ success: boolean; message: string }> =>
    httpClient.delete(`/api/companies/${id}`),

  /**
   * 啟用公司
   */
  activate: (id: number): Promise<Company> =>
    httpClient.post(`/api/companies/${id}/activate`),

  /**
   * 停用公司
   */
  deactivate: (id: number): Promise<Company> =>
    httpClient.post(`/api/companies/${id}/deactivate`),

  /**
   * 獲取公司統計
   */
  getStats: (id: number): Promise<CompanyStats> =>
    httpClient.get(`/api/companies/${id}/stats`),

  /**
   * 獲取公司用戶
   */
  getUsers: (id: number, params?: { page?: number; limit?: number }): Promise<{
    users: Array<{
      id: number
      email: string
      name: string
      role: string
      is_active: boolean
      created_at: string
    }>
    total: number
  }> =>
    httpClient.get(`/api/companies/${id}/users`, params),

  /**
   * 邀請用戶
   */
  inviteUser: (id: number, userData: { email: string; name: string; role: string }): Promise<{
    id: string
    company_id: number
    email: string
    name: string
    role: string
  }> =>
    httpClient.post(`/api/companies/${id}/invite`, userData),

  /**
   * 移除用戶
   */
  removeUser: (id: number, userId: number): Promise<{ success: boolean; message: string }> =>
    httpClient.delete(`/api/companies/${id}/users/${userId}`),

  /**
   * 更新用戶角色
   */
  updateUserRole: (id: number, userId: number, role: string): Promise<{
    id: number
    email: string
    name: string
    role: string
  }> =>
    httpClient.put(`/api/companies/${id}/users/${userId}/role`, { role }),

  /**
   * 更新 LINE 設定
   */
  updateLineSettings: (id: number, settings: {
    line_channel_token: string
    line_channel_secret: string
    line_bot_enabled: boolean
  }): Promise<Company> =>
    httpClient.put(`/api/companies/${id}/line-settings`, settings),

  /**
   * 測試 LINE 連線
   */
  testLineConnection: (id: number): Promise<{ success: boolean; message: string }> =>
    httpClient.post(`/api/companies/${id}/line-settings/test`),

  /**
   * 獲取 Webhook URL
   */
  getWebhookUrl: (companyCode: string): string => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    return `${baseUrl}/api/webhook/${companyCode}`
  },
}