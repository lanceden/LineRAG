/**
 * 用戶管理 API
 */

import { api } from './client'

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  last_login?: string
  created_at: string
  accessible_companies: Array<{
    id: number
    name: string
  }>
}

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  full_name: string
  role: string
}

export interface UpdateUserRequest {
  username?: string
  email?: string
  password?: string  // 可選的密碼更新
  full_name?: string
  role?: string
  is_active?: boolean
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  page_size: number
}

export interface UserStatsResponse {
  total_users: number
  active_users: number
  admin_users: number
  new_users_this_month: number
}

export const usersApi = {
  // 獲取用戶列表
  getUsers: (params: {
    page?: number
    page_size?: number
    role?: string
    search?: string
  } = {}): Promise<UserListResponse> => {
    return api.get<UserListResponse>('/api/system-users/', params)
  },

  // 創建用戶
  createUser: (userData: CreateUserRequest): Promise<User> => {
    return api.post<User>('/api/system-users/', userData)
  },

  // 更新用戶
  updateUser: (userId: number, userData: UpdateUserRequest): Promise<User> => {
    return api.put<User>(`/api/system-users/${userId}`, userData)
  },

  // 刪除用戶
  deleteUser: (userId: number): Promise<{ success: boolean; message: string }> => {
    return api.delete<{ success: boolean; message: string }>(`/api/system-users/${userId}`)
  },

  // 獲取用戶統計
  getUserStats: (): Promise<UserStatsResponse> => {
    return api.get<UserStatsResponse>('/api/system-users/stats')
  },

  // 授予公司權限
  grantCompanyAccess: (companyId: number, userId: number): Promise<{ success: boolean; message: string }> => {
    return api.post<{ success: boolean; message: string }>(
      `/api/system-users/companies/${companyId}/access`,
      { user_id: userId }
    )
  },

  // 撤銷公司權限
  revokeCompanyAccess: (companyId: number, userId: number): Promise<{ success: boolean; message: string }> => {
    return api.delete<{ success: boolean; message: string }>(
      `/api/system-users/companies/${companyId}/access/${userId}`
    )
  },
}