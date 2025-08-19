/**
 * 認證相關 API
 */

import { httpClient } from './httpClient'

export interface LoginCredentials {
  email: string
  password: string
}

export interface LoginResponse {
  success: boolean
  message: string
  access_token: string
  refresh_token?: string
  user: {
    id: number
    email: string
    full_name: string
    role: string
    is_active: boolean
  }
  accessible_companies: Array<{
    id: number
    name: string
    code: string
    is_active: boolean
  }>
}

export const authApi = {
  /**
   * 用戶登入
   */
  login: (credentials: LoginCredentials): Promise<LoginResponse> =>
    httpClient.post('/api/auth/login', credentials),

  /**
   * 驗證 token
   */
  validateToken: (token: string): Promise<{ valid: boolean; user_id?: number }> =>
    httpClient.post('/api/auth/validate-token', { token }),

  /**
   * 刷新 token
   */
  refreshToken: (refreshToken: string): Promise<{ access_token: string }> =>
    httpClient.post('/api/auth/refresh', { refresh_token: refreshToken }),

  /**
   * 登出
   */
  logout: (): Promise<{ success: boolean; message: string }> =>
    httpClient.post('/api/auth/logout'),
}