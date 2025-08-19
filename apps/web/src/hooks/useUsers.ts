/**
 * 用戶管理相關的 React hooks
 */

import { useState, useEffect } from 'react'
import { usersApi } from '@/lib/api/usersApi'
import type { User, UserListResponse, UserStatsResponse, CreateUserRequest, UpdateUserRequest } from '@/types/user'

// 用戶列表 hook
export function useUsers(params: {
  page?: number
  limit?: number
  search?: string
  is_active?: boolean
} = {}) {
  const [data, setData] = useState<UserListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await usersApi.getList(params)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [params.page, params.limit, params.search, params.is_active])

  return {
    data,
    loading,
    error,
    refetch: fetchUsers,
  }
}

// 用戶統計 hook
export function useUserStats() {
  const [data, setData] = useState<UserStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await usersApi.getStats()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user stats')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  return {
    data,
    loading,
    error,
    refetch: fetchStats,
  }
}

// 用戶操作 hook
export function useUserActions() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createUser = async (userData: CreateUserRequest): Promise<User | null> => {
    try {
      setLoading(true)
      setError(null)
      const result = await usersApi.create(userData)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user')
      return null
    } finally {
      setLoading(false)
    }
  }

  const updateUser = async (userId: number, userData: UpdateUserRequest): Promise<User | null> => {
    try {
      setLoading(true)
      setError(null)
      const result = await usersApi.update(userId, userData)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user')
      return null
    } finally {
      setLoading(false)
    }
  }

  const deleteUser = async (userId: number): Promise<boolean> => {
    try {
      setLoading(true)
      setError(null)
      await usersApi.delete(userId)
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user')
      return false
    } finally {
      setLoading(false)
    }
  }


  return {
    loading,
    error,
    createUser,
    updateUser,
    deleteUser,
  }
}