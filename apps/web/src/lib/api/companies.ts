/**
 * 公司管理 API 客戶端
 */

import { apiClient } from './client'
import type {
  Company,
  CreateCompanyRequest,
  UpdateCompanyRequest,
  CompanyListParams,
  CompanyListResponse,
  CompanyUser,
  CompanyUserListResponse,
  InviteUserRequest,
  CompanyInvitation,
  CompanyActivity,
  CompanyStats,
  CompanySettings,
  CompanyIntegration,
  CompanyExportOptions,
  CompanySearchResponse,
} from '@/types/company'

export class CompaniesApi {
  /**
   * 獲取公司列表 (使用現有的 admin API)
   */
  async getCompanies(params?: CompanyListParams): Promise<CompanyListResponse> {
    // 使用現有的 admin API，但需要轉換回應格式
    const response = await apiClient.get<Company[]>('/admin/companies', params)

    // 轉換為標準的分頁回應格式
    return {
      companies: response,
      total: response.length,
      page: params?.page || 1,
      limit: params?.limit || 20,
      has_next: false,
      has_prev: false,
    }
  }

  /**
   * 獲取單個公司詳情 (暫時使用列表 API 過濾)
   */
  async getCompany(companyId: string): Promise<Company> {
    const companies = await apiClient.get<Company[]>('/admin/companies')
    const company = companies.find(c => c.id.toString() === companyId)

    if (!company) {
      throw new Error('公司不存在')
    }

    return company
  }

  /**
   * 建立新公司
   */
  async createCompany(data: CreateCompanyRequest): Promise<Company> {
    return apiClient.post<Company>('/companies', data)
  }

  /**
   * 更新公司資訊
   */
  async updateCompany(companyId: string, data: UpdateCompanyRequest): Promise<Company> {
    return apiClient.put<Company>(`/companies/${companyId}`, data)
  }

  /**
   * 刪除公司
   */
  async deleteCompany(companyId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/companies/${companyId}`)
  }

  /**
   * 啟用公司
   */
  async activateCompany(companyId: string): Promise<Company> {
    return apiClient.post<Company>(`/companies/${companyId}/activate`)
  }

  /**
   * 停用公司
   */
  async deactivateCompany(companyId: string): Promise<Company> {
    return apiClient.post<Company>(`/companies/${companyId}/deactivate`)
  }

  /**
   * 獲取公司統計資訊
   */
  async getCompanyStats(companyId: string): Promise<CompanyStats> {
    return apiClient.get<CompanyStats>(`/companies/${companyId}/stats`)
  }

  /**
   * 獲取公司設定
   */
  async getCompanySettings(companyId: string): Promise<CompanySettings> {
    return apiClient.get<CompanySettings>(`/companies/${companyId}/settings`)
  }

  /**
   * 更新公司設定
   */
  async updateCompanySettings(companyId: string, settings: Partial<CompanySettings>): Promise<CompanySettings> {
    return apiClient.put<CompanySettings>(`/companies/${companyId}/settings`, settings)
  }

  /**
   * 獲取公司用戶列表
   */
  async getCompanyUsers(companyId: string, params?: { page?: number; limit?: number }): Promise<CompanyUserListResponse> {
    return apiClient.get<CompanyUserListResponse>(`/companies/${companyId}/users`, params)
  }

  /**
   * 邀請用戶加入公司
   */
  async inviteUser(companyId: string, data: InviteUserRequest): Promise<CompanyInvitation> {
    return apiClient.post<CompanyInvitation>(`/companies/${companyId}/invite`, data)
  }

  /**
   * 移除公司用戶
   */
  async removeUser(companyId: string, userId: number): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/companies/${companyId}/users/${userId}`)
  }

  /**
   * 更新用戶角色
   */
  async updateUserRole(companyId: string, userId: number, role: string): Promise<CompanyUser> {
    return apiClient.put<CompanyUser>(`/companies/${companyId}/users/${userId}/role`, { role })
  }

  /**
   * 獲取公司邀請列表
   */
  async getInvitations(companyId: string): Promise<CompanyInvitation[]> {
    return apiClient.get<CompanyInvitation[]>(`/companies/${companyId}/invitations`)
  }

  /**
   * 取消邀請
   */
  async cancelInvitation(companyId: string, invitationId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/companies/${companyId}/invitations/${invitationId}`)
  }

  /**
   * 重新發送邀請
   */
  async resendInvitation(companyId: string, invitationId: string): Promise<CompanyInvitation> {
    return apiClient.post<CompanyInvitation>(`/companies/${companyId}/invitations/${invitationId}/resend`)
  }

  /**
   * 獲取公司活動記錄
   */
  async getCompanyActivities(companyId: string, params?: { page?: number; limit?: number }): Promise<{ activities: CompanyActivity[]; total: number }> {
    return apiClient.get<{ activities: CompanyActivity[]; total: number }>(`/companies/${companyId}/activities`, params)
  }

  /**
   * 獲取公司整合設定
   */
  async getIntegrations(companyId: string): Promise<CompanyIntegration[]> {
    return apiClient.get<CompanyIntegration[]>(`/companies/${companyId}/integrations`)
  }

  /**
   * 建立整合設定
   */
  async createIntegration(companyId: string, data: Omit<CompanyIntegration, 'id' | 'company_id' | 'created_at' | 'updated_at'>): Promise<CompanyIntegration> {
    return apiClient.post<CompanyIntegration>(`/companies/${companyId}/integrations`, data)
  }

  /**
   * 更新整合設定
   */
  async updateIntegration(companyId: string, integrationId: string, data: Partial<CompanyIntegration>): Promise<CompanyIntegration> {
    return apiClient.put<CompanyIntegration>(`/companies/${companyId}/integrations/${integrationId}`, data)
  }

  /**
   * 刪除整合設定
   */
  async deleteIntegration(companyId: string, integrationId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/companies/${companyId}/integrations/${integrationId}`)
  }

  /**
   * 測試整合連接
   */
  async testIntegration(companyId: string, integrationId: string): Promise<{ success: boolean; message: string; details?: any }> {
    return apiClient.post<{ success: boolean; message: string; details?: any }>(`/companies/${companyId}/integrations/${integrationId}/test`)
  }

  /**
   * 搜尋公司
   */
  async searchCompanies(query: string, options?: { limit?: number; filters?: Record<string, any> }): Promise<CompanySearchResponse> {
    return apiClient.post<CompanySearchResponse>('/companies/search', { query, ...options })
  }

  /**
   * 匯出公司資料
   */
  async exportCompanies(options: CompanyExportOptions): Promise<{ export_id: string; download_url?: string }> {
    return apiClient.post<{ export_id: string; download_url?: string }>('/companies/export', options)
  }

  /**
   * 獲取匯出狀態
   */
  async getExportStatus(exportId: string): Promise<{ status: string; download_url?: string; error?: string }> {
    return apiClient.get<{ status: string; download_url?: string; error?: string }>(`/companies/exports/${exportId}`)
  }

  /**
   * 上傳公司 Logo
   */
  async uploadLogo(companyId: string, file: File): Promise<{ logo_url: string }> {
    const formData = new FormData()
    formData.append('logo', file)

    return apiClient.request<{ logo_url: string }>(`/companies/${companyId}/logo`, {
      method: 'POST',
      body: formData,
    })
  }

  /**
   * 刪除公司 Logo
   */
  async deleteLogo(companyId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/companies/${companyId}/logo`)
  }

  /**
   * 複製公司設定
   */
  async duplicateCompany(companyId: string, newName: string): Promise<Company> {
    return apiClient.post<Company>(`/companies/${companyId}/duplicate`, { name: newName })
  }

  /**
   * 批次操作公司
   */
  async batchOperation(operation: 'activate' | 'deactivate' | 'delete', companyIds: string[]): Promise<{ success: number; failed: number; errors?: Array<{ id: string; error: string }> }> {
    return apiClient.post<{ success: number; failed: number; errors?: Array<{ id: string; error: string }> }>('/companies/batch', {
      operation,
      company_ids: companyIds,
    })
  }
}

// 創建默認實例
export const companiesApi = new CompaniesApi()

// 便捷方法
export const companies = {
  list: (params?: CompanyListParams) => companiesApi.getCompanies(params),
  get: (id: string) => companiesApi.getCompany(id),
  create: (data: CreateCompanyRequest) => companiesApi.createCompany(data),
  update: (id: string, data: UpdateCompanyRequest) => companiesApi.updateCompany(id, data),
  delete: (id: string) => companiesApi.deleteCompany(id),
  activate: (id: string) => companiesApi.activateCompany(id),
  deactivate: (id: string) => companiesApi.deactivateCompany(id),
  stats: (id: string) => companiesApi.getCompanyStats(id),
  settings: {
    get: (id: string) => companiesApi.getCompanySettings(id),
    update: (id: string, settings: Partial<CompanySettings>) => companiesApi.updateCompanySettings(id, settings),
  },
  users: {
    list: (id: string, params?: any) => companiesApi.getCompanyUsers(id, params),
    invite: (id: string, data: InviteUserRequest) => companiesApi.inviteUser(id, data),
    remove: (id: string, userId: number) => companiesApi.removeUser(id, userId),
    updateRole: (id: string, userId: number, role: string) => companiesApi.updateUserRole(id, userId, role),
  },
  invitations: {
    list: (id: string) => companiesApi.getInvitations(id),
    cancel: (id: string, invitationId: string) => companiesApi.cancelInvitation(id, invitationId),
    resend: (id: string, invitationId: string) => companiesApi.resendInvitation(id, invitationId),
  },
  activities: (id: string, params?: any) => companiesApi.getCompanyActivities(id, params),
  integrations: {
    list: (id: string) => companiesApi.getIntegrations(id),
    create: (id: string, data: any) => companiesApi.createIntegration(id, data),
    update: (id: string, integrationId: string, data: any) => companiesApi.updateIntegration(id, integrationId, data),
    delete: (id: string, integrationId: string) => companiesApi.deleteIntegration(id, integrationId),
    test: (id: string, integrationId: string) => companiesApi.testIntegration(id, integrationId),
  },
  search: (query: string, options?: any) => companiesApi.searchCompanies(query, options),
  export: (options: CompanyExportOptions) => companiesApi.exportCompanies(options),
  logo: {
    upload: (id: string, file: File) => companiesApi.uploadLogo(id, file),
    delete: (id: string) => companiesApi.deleteLogo(id),
  },
  duplicate: (id: string, newName: string) => companiesApi.duplicateCompany(id, newName),
  batch: (operation: 'activate' | 'deactivate' | 'delete', ids: string[]) => companiesApi.batchOperation(operation, ids),
}
