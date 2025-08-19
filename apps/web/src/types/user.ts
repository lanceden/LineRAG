/**
 * 用戶管理相關類型定義 - 基於新權限系統
 */

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_active: boolean
  last_login?: string
  created_at: string
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
  inactive_users: number
  users_this_month: number
}

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  full_name: string
}

export interface UpdateUserRequest {
  username?: string
  email?: string
  password?: string
  full_name?: string
  is_active?: boolean
}

// 新增權限系統相關類型
export interface Permission {
  id: number
  category: string
  name: string
  code: string
  description?: string
}

export interface UserPermission {
  id: number
  user_id: number
  granted_permissions: string[]  // 權限代碼陣列
  accessible_companies: string[] // 公司ID陣列，"*"表示全部
  created_at: string
  updated_at: string
}

export interface UserPermissionRequest {
  user_id: number
  granted_permissions: string[]
  accessible_companies: string[]
}

export interface PermissionMatrix {
  categories: Array<{
    name: string
    permissions: Array<{
      code: string
      name: string
      description?: string
    }>
  }>
}

export interface Company {
  id: number
  name: string
  code: string
  is_active: boolean
}