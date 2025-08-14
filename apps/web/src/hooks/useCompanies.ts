/**
 * 公司管理相關 hooks
 */

import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api/client'
import type {
  Company,
  CompanyListParams,
  CompanyListResponse,
  CreateCompanyRequest,
  UpdateCompanyRequest,
  CompanyStats,
  CompanySettings,
  CompanyUser,
  CompanyUserListResponse,
  InviteUserRequest,
} from '@/types/company'

/**
 * 公司列表管理 hook
 */
export function useCompanies(params?: CompanyListParams) {
  const [data, setData] = useState<CompanyListResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCompanies = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // 使用統一 API 獲取公司列表
      const companies = await api.admin.getCompanies()

      // 轉換為標準的分頁回應格式
      const response: CompanyListResponse = {
        companies,
        total: companies.length,
        page: params?.page || 1,
        limit: params?.limit || 20,
        has_next: false,
        has_prev: false,
      }

      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取公司列表失敗')
    } finally {
      setLoading(false)
    }
  }, [params])

  useEffect(() => {
    fetchCompanies()
  }, [fetchCompanies])

  const refresh = useCallback(() => {
    fetchCompanies()
  }, [fetchCompanies])

  return {
    companies: data?.companies || [],
    total: data?.total || 0,
    page: data?.page || 1,
    limit: data?.limit || 20,
    hasNext: data?.has_next || false,
    hasPrev: data?.has_prev || false,
    loading,
    error,
    refresh,
  }
}

/**
 * 單個公司管理 hook
 */
export function useCompany(companyId: string | null) {
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCompany = useCallback(async () => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.get(companyId)
      setCompany(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取公司資訊失敗')
    } finally {
      setLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchCompany()
  }, [fetchCompany])

  const refresh = useCallback(() => {
    fetchCompany()
  }, [fetchCompany])

  return {
    company,
    loading,
    error,
    refresh,
  }
}

/**
 * 公司操作 hook
 */
export function useCompanyOperations() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createCompany = useCallback(async (data: CreateCompanyRequest) => {
    setLoading(true)
    setError(null)

    try {
      const response = await companies.create(data)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '建立公司失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  const updateCompany = useCallback(async (companyId: string, data: UpdateCompanyRequest) => {
    setLoading(true)
    setError(null)

    try {
      const response = await companies.update(companyId, data)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '更新公司失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteCompany = useCallback(async (companyId: string) => {
    setLoading(true)
    setError(null)

    try {
      const response = await companies.delete(companyId)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '刪除公司失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  const activateCompany = useCallback(async (companyId: string) => {
    setLoading(true)
    setError(null)

    try {
      const response = await companies.activate(companyId)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '啟用公司失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  const deactivateCompany = useCallback(async (companyId: string) => {
    setLoading(true)
    setError(null)

    try {
      const response = await companies.deactivate(companyId)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '停用公司失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    createCompany,
    updateCompany,
    deleteCompany,
    activateCompany,
    deactivateCompany,
    loading,
    error,
  }
}

/**
 * 公司統計資訊 hook
 */
export function useCompanyStats(companyId: string | null) {
  const [stats, setStats] = useState<CompanyStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.stats(companyId)
      setStats(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取統計資訊失敗')
    } finally {
      setLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  const refresh = useCallback(() => {
    fetchStats()
  }, [fetchStats])

  return {
    stats,
    loading,
    error,
    refresh,
  }
}

/**
 * 公司設定管理 hook
 */
export function useCompanySettings(companyId: string | null) {
  const [settings, setSettings] = useState<CompanySettings | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = useCallback(async () => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.settings.get(companyId)
      setSettings(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取公司設定失敗')
    } finally {
      setLoading(false)
    }
  }, [companyId])

  const updateSettings = useCallback(async (newSettings: Partial<CompanySettings>) => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.settings.update(companyId, newSettings)
      setSettings(response)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '更新公司設定失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  const refresh = useCallback(() => {
    fetchSettings()
  }, [fetchSettings])

  return {
    settings,
    updateSettings,
    loading,
    error,
    refresh,
  }
}

/**
 * 公司用戶管理 hook
 */
export function useCompanyUsers(companyId: string | null) {
  const [data, setData] = useState<CompanyUserListResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchUsers = useCallback(async () => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.users.list(companyId)
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取用戶列表失敗')
    } finally {
      setLoading(false)
    }
  }, [companyId])

  const inviteUser = useCallback(async (userData: InviteUserRequest) => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.users.invite(companyId, userData)
      await fetchUsers() // 重新獲取用戶列表
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '邀請用戶失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [companyId, fetchUsers])

  const removeUser = useCallback(async (userId: number) => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.users.remove(companyId, userId)
      await fetchUsers() // 重新獲取用戶列表
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '移除用戶失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [companyId, fetchUsers])

  const updateUserRole = useCallback(async (userId: number, role: string) => {
    if (!companyId) return

    setLoading(true)
    setError(null)

    try {
      const response = await companies.users.updateRole(companyId, userId, role)
      await fetchUsers() // 重新獲取用戶列表
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '更新用戶角色失敗'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [companyId, fetchUsers])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const refresh = useCallback(() => {
    fetchUsers()
  }, [fetchUsers])

  return {
    users: data?.users || [],
    total: data?.total || 0,
    inviteUser,
    removeUser,
    updateUserRole,
    loading,
    error,
    refresh,
  }
}
