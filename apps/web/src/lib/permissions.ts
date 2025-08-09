/**
 * 權限管理工具
 */
import { useSession } from 'next-auth/react'
import { useState, useEffect } from 'react'

export interface User {
  line_id: string
  name: string
  email: string
  role: 'admin' | 'cs'
  is_active: boolean
  created_at: number
  updated_at: number
}

export interface ApiResponse {
  success: boolean
  message: string
  user?: User
}

/**
 * 權限檢查函數
 */
export function hasPermission(userRole?: string, requiredRole: 'admin' | 'cs' = 'cs'): boolean {
  if (!userRole) return false
  
  if (requiredRole === 'cs') {
    return ['admin', 'cs'].includes(userRole)
  }
  
  return userRole === 'admin'
}

/**
 * React Hook for permissions
 */
export function usePermissions() {
  const { data: session, status } = useSession()
  
  return {
    isLoading: status === 'loading',
    isAuthenticated: !!session,
    user: session?.user,
    isAdmin: session?.user?.role === 'admin',
    isCS: hasPermission(session?.user?.role),
    hasRole: (role: 'admin' | 'cs') => hasPermission(session?.user?.role, role),
    canManageUsers: session?.user?.role === 'admin',
    canViewDashboard: hasPermission(session?.user?.role, 'cs')
  }
}

/**
 * API 呼叫函數
 */
const API_BASE = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000'

export async function fetchUsers(): Promise<User[]> {
  const response = await fetch(`${API_BASE}/users/`)
  if (!response.ok) throw new Error('Failed to fetch users')
  return response.json()
}

export async function createUser(userData: {
  line_id: string
  name: string
  email?: string
  role?: 'admin' | 'cs'
}): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE}/users/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  })
  
  if (!response.ok) throw new Error('Failed to create user')
  return response.json()
}

export async function updateUserRole(lineId: string, role: 'admin' | 'cs'): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE}/users/${lineId}/role`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role })
  })
  
  if (!response.ok) throw new Error('Failed to update user role')
  return response.json()
}

export async function deactivateUser(lineId: string): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE}/users/${lineId}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) throw new Error('Failed to deactivate user')
  return response.json()
}

export async function checkPermission(lineId: string, requiredRole: 'admin' | 'cs'): Promise<{
  line_id: string
  required_role: string
  has_permission: boolean
}> {
  const response = await fetch(`${API_BASE}/users/check/${lineId}/permission?required_role=${requiredRole}`)
  if (!response.ok) throw new Error('Failed to check permission')
  return response.json()
}