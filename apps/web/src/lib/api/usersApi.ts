/**
 * 用戶管理 API - 基於新權限系統
 */

import { httpClient } from './httpClient'
import type {
  User,
  UserListResponse,
  UserStatsResponse,
  CreateUserRequest,
  UpdateUserRequest,
  Permission,
  UserPermission,
  UserPermissionRequest,
  PermissionMatrix,
} from '@/types/user'

export const usersApi = {
  /**
   * 獲取用戶列表
   */
  getList: (params: {
    page?: number
    limit?: number
    search?: string
    is_active?: boolean
  } = {}): Promise<UserListResponse> =>
    httpClient.get('/api/system-users/', params),

  /**
   * 獲取單個用戶詳情
   */
  getById: (userId: number): Promise<User> =>
    httpClient.get(`/api/system-users/${userId}`),

  /**
   * 創建用戶
   */
  create: (userData: CreateUserRequest): Promise<User> =>
    httpClient.post('/api/system-users/', userData),

  /**
   * 更新用戶基本信息
   */
  update: (userId: number, userData: UpdateUserRequest): Promise<User> =>
    httpClient.put(`/api/system-users/${userId}`, userData),

  /**
   * 刪除用戶
   */
  delete: (userId: number): Promise<{ message: string }> =>
    httpClient.delete(`/api/system-users/${userId}`),

  /**
   * 啟用用戶
   */
  activate: (userId: number): Promise<{ message: string }> =>
    httpClient.post(`/api/system-users/${userId}/activate`),

  /**
   * 停用用戶
   */
  deactivate: (userId: number): Promise<{ message: string }> =>
    httpClient.post(`/api/system-users/${userId}/deactivate`),

  /**
   * 獲取用戶統計
   */
  getStats: (): Promise<UserStatsResponse> =>
    httpClient.get('/api/system-users/stats'),
}

// 權限管理相關API
export const permissionsApi = {
  /**
   * 獲取所有可用權限
   */
  getAllPermissions: (): Promise<Permission[]> =>
    httpClient.get('/api/permissions/'),

  /**
   * 獲取權限矩陣結構
   */
  getPermissionMatrix: (): Promise<PermissionMatrix> =>
    httpClient.get('/api/permissions/matrix'),

  /**
   * 獲取用戶權限
   */
  getUserPermissions: (userId: number): Promise<UserPermission> =>
    httpClient.get(`/api/permissions/user/${userId}`),

  /**
   * 更新用戶權限
   */
  updateUserPermissions: (permissionData: UserPermissionRequest): Promise<UserPermission> =>
    httpClient.put(`/api/permissions/user/${permissionData.user_id}`, permissionData),

  /**
   * 批量獲取多個用戶的權限摘要
   */
  getUsersPermissionsSummary: (userIds: number[]): Promise<Array<{
    user_id: number
    permissions_count: number
    companies_count: number
    has_all_companies: boolean
  }>> =>
    httpClient.post('/api/permissions/users/summary', { user_ids: userIds }),
}
